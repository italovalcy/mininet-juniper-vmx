#!/usr/bin/python3
from mininet.net import Mininet
from mininet.node import RemoteController
from mininet.cli import CLI
from mininet.log import setLogLevel, info
from mininet.topo import Topo

from mininet_juniper_vmx import VMXSwitch


class JunosOvsTopo(Topo):
    def build( self, **_kwargs ):
        VMXSwitch.publish_driver = "ip"
        VMXSwitch.publish_ip_net = "LOCALNET"
        VMXSwitch.publish_ip_intf = "eth0"
        s1 = self.addSwitch('s1')
        s2 = self.addSwitch('s2', cls=VMXSwitch, init_config="/configs/s2.txt")
        s3 = self.addSwitch('s3', cls=VMXSwitch, init_config="/configs/s3.txt")
        s4 = self.addSwitch('s4', cls=VMXSwitch, init_config="/configs/s4.txt")
        s5 = self.addSwitch('s5')
        h1 = self.addHost('h1', mac='00:00:00:00:00:01')
        h2 = self.addHost('h2', mac='00:00:00:00:00:02')
        h3 = self.addHost('h3', mac='00:00:00:00:00:03')
        h4 = self.addHost('h4', mac='00:00:00:00:00:04')
        h5 = self.addHost('h5', mac='00:00:00:00:00:05')
        self.addLink(h1, s1)
        self.addLink(h2, s2)
        self.addLink(h3, s3)
        self.addLink(h4, s4)
        self.addLink(h5, s5)
        self.addLink(s1, s2)
        self.addLink(s2, s3)
        self.addLink(s3, s4)
        self.addLink(s4, s5)
        self.addLink(s2, s4)

# You can run any of the topologies above by doing:
# mn --custom junos_ovs-example-topo.py --topo junos_ovs --controller=remote,ip=127.0.0.1
topos = {
    'junos_ovs': (lambda: JunosOvsTopo()),
}

def runJunosOvsTopo():
    "Create and run my topo"
    topo = JunosOvsTopo()
    net = Mininet( topo=topo )
    net.start()
    CLI( net )
    net.stop()


if __name__ == '__main__':
    setLogLevel( 'info' )
    runJunosOvsTopo()
