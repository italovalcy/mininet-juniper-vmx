# Mininet Juniper vMX

This repo provides a very simplified integration between Mininet and Juniper vMX switches for the AtlanticWave-SDX project. Juniper vMX switches are based on Junos 14.xx, which is an old version still allowing control plane and data plane functions to run on the same qemu instance.

You will have to download the correct Junos vMX image to make this work. We tested with JUNOS 14.1R1.10. Once you have downloaded Junos, please save it into `hda.qcow2` in this very same folder where README.md is.

An example topology is also provided, and you can run it with:
```
docker run -d --name mn-junos-mx --privileged -v ${PWD}/junos_ovs-example-topo.py:/topo.py ghcr.io/atlanticwave-sdx/mininet-juniper-vmx:latest --custom /topo.py --topo junos_ovs --controller=remote,ip=127.0.0.1
```

## Requirements

The host that runs this experiment must have the following Linux Kernel modules loaded:
- openvswitch
- kvm

Also, make sure you can run virtualization on your host (nested virtualization with kvm) -- output below should not be empty:
```
egrep 'vmx|svm' /proc/cpuinfo
```
