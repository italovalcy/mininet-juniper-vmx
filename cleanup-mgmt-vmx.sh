#!/bin/bash

PUBLISH_DRIVER=$1
PUBLISH_IP_INTF=$2

if ovs-vsctl list-br | grep -q br-vmx-mgmt; then
	ovs-vsctl del-br br-vmx-mgmt
fi
if [ "$PUBLISH_DRIVER" = "ip" ]; then
	ip -4 addr flush dev $PUBLISH_IP_INTF scope link
fi
iptables -t nat -D POSTROUTING -o br-vmx-mgmt -j MASQUERADE
iptables -t nat -D PREROUTING -j VMX-PRE
iptables -t nat -F VMX-PRE
iptables -t nat -X VMX-PRE
