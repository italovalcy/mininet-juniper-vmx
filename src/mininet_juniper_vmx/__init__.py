"""
apt-get install -y qemu-system-x86_64 expect netcat

--> qemu_wrapper
git clone https://github.com/dainok/unetlab
cd unetlab/wrappers/
apt-get install make g++
make
/opt/unetlab/wrappers/qemu_wrapper --help
"""
import sys
import uuid
import ipaddress

import mininet.clean as Cleanup
from mininet.net import Mininet
from mininet.node import RemoteController
from mininet.node import Switch, OVSSwitch
from mininet.cli import CLI
from mininet.log import setLogLevel, info
from mininet.topo import Topo
from mininet.moduledeps import moduleDeps, pathCheck

from nornir import InitNornir
from nornir_netmiko.tasks import netmiko_send_command
from nornir_utils.plugins.functions import print_result


VMX_IMG = "/opt/vmx/hda.qcow2" 

class VMXSwitch( Switch ):
    "Juniper vMX Node"
    sw_id_inc = 1
    portBase  = 0  # juniper switches start with port 0 (ge-0/0/0)
    publish_driver = "none"
    publish_ip_net = "LOCALNET"
    publish_ip_intf = "eth0"

    def __init__( self, name, verbose=False, init_config="/dev/null", publish_driver=None, publish_ip_net=None, publish_ip_intf=None, **kwargs ):
        Switch.__init__( self, name, **kwargs )
        self.verbose = verbose
        self.init_config = init_config
        # publish_driver: Publish strategy for the vMX, can be: none, port, ip
        #
        # none: (default) will not provide any proxy to ther vMX nodes
        # port: will provide a port-based NAT (Network Address Translation) for netconf/ssh ports
        #   each vMX host will have a different port starting on 8300 and 2200 and
        #   incrementing based on the switch ID (ie. first vMX will be 8301 -> 830 and
        #   2201 -> 22, second vMX will be 8302 -> 830 and 2202 -> 22, so on)
        # ip: will provide an IP-based NAT for each vMX host. The external IP and 
        #   external interface can be specified with publish_ip_net and publish_ip_intf.
        #   Example:
        #
        #   publish_driver="ip", publish_ip_net="10.255.255.0/24", publish_ip_intf="eth0"
        #
        #   In the example above, each vMX will have an IP of the range 10.255.255.xx published
        #   on the eth0 (can be accessed with the link scope)
        self.publish_driver = publish_driver if publish_driver else VMXSwitch.publish_driver
        self.publish_ip_net = publish_ip_net if publish_ip_net else VMXSwitch.publish_ip_net
        self.publish_ip_intf = publish_ip_intf if publish_ip_intf else VMXSwitch.publish_ip_intf
        self.myuuid = uuid.uuid4()
        self.myswid = VMXSwitch.sw_id_inc
        VMXSwitch.sw_id_inc += 1

    @classmethod
    def setup( cls ):
        "Make sure qemu is installed"
        pathCheck( 'qemu-system-x86_64',
                   moduleName="Juniper vMX" )

    @classmethod
    def batchShutdown( cls, switches ):
        "Kill each vMX switch, to be waited on later in stop()"
        info("batch stop switches %s\n" % [s.name for s in switches])
        Cleanup.sh("pkill -f qemu-system-x86_64")
        Cleanup.sh("ovs-vsctl list-br | grep br-vmx | xargs -rl ovs-vsctl del-br")
        Cleanup.sh("rm -f /tmp/vmx-*")
        Cleanup.sh("ip link show | egrep -o 'vmx-[^:]+' | xargs -r -l ip link del")
        Cleanup.sh("/opt/vmx/cleanup-mgmt-vmx.sh %s %s 2>/dev/null" % (cls.publish_driver, cls.publish_ip_intf))
        return switches

    def start( self, controllers ):
        "Start up a new vMX switch"
        # make sure mgmt is setup
        self.cmd("/opt/vmx/setup-mgmt-vmx.sh 2>/dev/null")
        # config node
        info("\nstart %s" % self.name)
        self.cmd("echo starting > /tmp/vmx-status-%s" % self.name)
        self.cmd("ovs-vsctl add-br br-vmx-%s -- set Bridge br-vmx-%s fail-mode=secure" % (self.name, self.name))
        self.cmd("qemu-img create -F qcow2 -b %s -f qcow2 /tmp/vmx-%s.qcow2" % (VMX_IMG, self.name))
        # prepare command to be executed
        start_cmd = "tmux new-sess -d -s vmx-%s qemu-system-x86_64 -uuid %s -nographic" % (self.name, self.myuuid)
        #start_cmd = "/opt/unetlab/wrappers/qemu_wrapper -T 0 -D %d -t vmx-%s -F /usr/bin/qemu-system-x86_64 -- -uuid %s -nographic" % (self.myswid, self.name, self.myuuid)
        start_cmd += " -smp 1 -m 4096 -name %s -hda /tmp/vmx-%s.qcow2 -machine type=pc,accel=kvm -serial mon:stdio -nographic" % (self.name, self.name)
        #start_cmd += " -chardev socket,id=charserial0,host=127.0.0.1,port=%d,telnet,server,nowait -device isa-serial,chardev=charserial0,id=serial0" % (8700+self.myswid)
        #
        # this should allow us to connect into the monitor interface and shutdown the interface
        # as per https://lists.gnu.org/archive/html/qemu-discuss/2017-01/msg00103.html
        # echo "set_link virtio-net-pci.0 off" | socat - UNIX-CONNECT:<pathto your monitor socket>
        #
        start_cmd += " -monitor telnet:127.0.0.1:%d,server,nowait" % (50000+self.myswid)
        i = 0
        # first two interfaces are used by vMX for control (net0 will be mgmt and net1 internal connection)
        for _ in range(2):
            self.cmd("ip tuntap add mode tap vmx-%s-tap%d" % (self.name, i))
            self.cmd("ip link set up vmx-%s-tap%d" % (self.name, i))
            start_cmd += " -device virtio-net-pci,netdev=net%d,mac=50:00:00:%02x:00:%02x -netdev tap,id=net%d,ifname=vmx-%s-tap%d,script=no" % (i, self.myswid, i, i, self.name, i)
            i+=1
        self.cmd("ovs-vsctl add-port br-vmx-mgmt vmx-%s-tap0" % (self.name))
        for port in sorted(self.intfs.keys()):
            intf = self.intfs[port]
            if intf.name == "lo":
                continue
            info("\n-->add intf %s" % intf.name)
            self.cmd("ip tuntap add mode tap vmx-%s-tap%d" % (self.name, i))
            self.cmd("ip link set up vmx-%s-tap%d" % (self.name, i))
            self.cmd("ovs-vsctl add-port br-vmx-%s vmx-%s-tap%d" % (self.name, self.name, i))
            self.cmd("ovs-vsctl add-port br-vmx-%s %s" % (self.name, intf.name))
            self.cmd("ovs-ofctl add-flow br-vmx-%s in_port=%s,actions=output:vmx-%s-tap%d" % (self.name, intf.name, self.name, i))
            self.cmd("ovs-ofctl add-flow br-vmx-%s in_port=vmx-%s-tap%d,actions=output:%s" % (self.name, self.name, i, intf.name))
            start_cmd += " -device virtio-net-pci,netdev=net%d,mac=50:00:00:%02x:00:%02x -netdev tap,id=net%d,ifname=vmx-%s-tap%d,script=no" % (i, self.myswid, i, i, self.name, i)
            i+=1

        info("\nstart_cmd=%s" % start_cmd)
        self.cmd(start_cmd)
        self.cmd("/opt/vmx/setup-basic-vmx.sh %d %s %s %s %s %s >/tmp/vmx-%s.log 2>&1 &" % (self.myswid, self.name, self.init_config, self.publish_driver, self.publish_ip_net, self.publish_ip_intf, self.name))

    def stop( self, deleteIntfs=True ):
        """Terminate vMX switch.
           deleteIntfs: delete interfaces? (True)"""
        super( VMXSwitch, self ).stop( deleteIntfs )

    def attach( self, intf ):
        "Connect a data port"
        info("Not-Implemented: attach interface to %s if=%s" % (self.name, intf))

    def detach( self, intf ):
        "Disconnect a data port"
        info("Not-Implemented: disconnect interface to %s if=%s" % (self.name, intf))

    def dpctl( self, *args ):
        "Run dpctl command"
        nr = InitNornir(
            inventory={
                "plugin": "SimpleInventory",
                "options": {
                    "host_file": "/tmp/vmx-hosts.yaml",
                    "group_file": "/opt/vmx/nornir/vmx-group.yaml"
                },
            },
        )
        nr = nr.filter(name=self.name)
        results = nr.run(
            task=netmiko_send_command, command_string=" ".join(args)
        )
        return(results[self.name][0].result)

    def is_ready(self):
        """Check if switch is ready."""
        return self.cmd("cat /tmp/vmx-status-%s" % self.name).strip() == "ok"
