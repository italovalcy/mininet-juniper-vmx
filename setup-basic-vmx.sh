#!/bin/bash

TENANT_ID=0
DEVICE_ID=$1
DEVICE_NAME=$2
INIT_CONFIG=$3
PUBLISH_DRIVER=$4
PUBLISH_IP_NET=$5
PUBLISH_IP_INTF=$6

echo "$(date) starting $0 with ARGs: $@"

# from qemu_wrapper.c
# ts_port = 32768 + 128 * tenant_id + device_id;
CONSOLE_PORT=$((32768 + 128 * $TENANT_ID + $DEVICE_ID))

IP="192.168.56.$((100+$DEVICE_ID))"

sleep 5

echo "$(date) waiting for login prompt ..."
while ! tmux capture-pane -t vmx-$DEVICE_NAME -p 2>/dev/null | grep -q login:;
do
	sleep 1
done
echo "lab
lab123
configure
delete logical-systems
delete interfaces em0
set interfaces em0 unit 0 family inet address $IP/24
set system host-name $DEVICE_NAME
set system services ssh
commit
exit" | while read LINE; do tmux send-keys -t vmx-$DEVICE_NAME "$LINE" Enter; sleep 3; done
#/usr/bin/expect <<EOF
#set timeout -1
#spawn telnet 127.0.0.1 $CONSOLE_PORT
#send -- "\r"
#expect "login:"
#EOF

#echo "Basic config file to provision the vMX ..."
#echo "lab
#lab123
#configure
#delete interfaces em0
#set interfaces em0 unit 0 family inet address $IP/24
#commit
#exit
#exit
#" | nc -t -i 1 -q 1 127.0.0.1 $CONSOLE_PORT

#init config will be done via nornir
#if [ -n "$INIT_CONFIG" -a -s "$INIT_CONFIG" ]; then
#	cat $INIT_CONFIG | while read LINE; do tmux send-keys -t vmx-$DEVICE_NAME "$LINE" Enter; sleep 3; done 
#fi
tmux send-keys -t vmx-$DEVICE_NAME "exit" Enter;
echo "$(date) Finished applying initial configs"

# To allow remote access to the VMX devices we have two approaches:
# 1) Destination NAT by port
# 2) Destination NAT by IP (aka Publish IP)
#
# The best approach would be Publish IP (Destination NAT by IP), which means that
# any request to the Published IP will be translated to the internal VMX mgmt IP. This is preferred
# because systems like OESS require a unique IP per VMX device.
#
# Destination NAT by port will be the fall back alternative when Proxy IP is not
# requested, which means that Netconf and SSH ports will be translated from incremental numbers
# based on the Device ID, i.e. first vMX device will be 8301 -> 830 and 2201 -> 22, and so on.
if [ "$PUBLISH_DRIVER" = "port" ]; then
	echo "$(date) Publish driver = port, creating iptables rules"
	iptables -t nat -A VMX-PRE -p tcp --dport $((8300+$DEVICE_ID)) -j DNAT --to $IP:830
	iptables -t nat -A VMX-PRE -p tcp --dport $((2200+$DEVICE_ID)) -j DNAT --to $IP:22
elif [ "$PUBLISH_DRIVER" = "ip" ]; then
	PROXY_MASK=$(echo "$PUBLISH_IP_NET" | cut -d"/" -f2)
	if [ "$PUBLISH_IP_NET" = "LOCALNET" ]; then
		PUBLISH_IP_NET=$(LANG=C ip -4 route show dev $PUBLISH_IP_INTF scope link | head -n1 | cut -d" " -f1)
		PROXY_MASK=32
	fi
	PROXY_IP=$(python3 -c "import ipaddress; print(ipaddress.ip_address(int(ipaddress.ip_network('$PUBLISH_IP_NET').broadcast_address) - $DEVICE_ID))")
	echo "$(date) Publish driver = ip applying configs for proxy IP $PROXY_IP"
	ip -4 addr add $PROXY_IP/$PROXY_MASK dev $PUBLISH_IP_INTF scope link
	iptables -t nat -A VMX-PRE -d $PROXY_IP -j DNAT --to $IP
fi

if [ ! -f /tmp/vmx-hosts.yaml ]; then
	echo "# vmx-hosts.yaml"  >> /tmp/vmx-hosts.yaml
	echo "---"               >> /tmp/vmx-hosts.yaml
fi

echo "
$DEVICE_NAME:
  hostname: $IP
  groups: [juniper_vmx]
" >> /tmp/vmx-hosts.yaml

if [ -n "$INIT_CONFIG" -a -s "$INIT_CONFIG" ]; then
	echo "$(date) Apply user config with nornir based on $INIT_CONFIG"
	python3 /opt/vmx/nornir/set-config-file.py --name $DEVICE_NAME $INIT_CONFIG
fi

echo "$(date) All done for $DEVICE_NAME"
echo ok > /tmp/vmx-status-$DEVICE_NAME
