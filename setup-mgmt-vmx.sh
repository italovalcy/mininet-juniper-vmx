#!/bin/bash

if ! ovs-vsctl list-br | grep -q br-vmx-mgmt; then
        ovs-vsctl add-br br-vmx-mgmt
        ip link set up br-vmx-mgmt
        ip addr add 192.168.56.254/24 dev br-vmx-mgmt
        iptables -t nat -A POSTROUTING -o br-vmx-mgmt -j MASQUERADE
        iptables -t nat -N VMX-PRE
        iptables -t nat -A PREROUTING -j VMX-PRE
fi
