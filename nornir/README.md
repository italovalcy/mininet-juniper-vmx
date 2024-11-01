# Overview

This repo contains some examples and config files that were built while studying/evaluationg Nornir as
an orchestration tool for Juniper devices. The subdirectory `examples/` contains such tests.

To be used with Mininet, the important files are:
- `vmx-group.yaml` (which should be placed into `/opt/vmx/nornir/vmx-group.yaml`): this file contains general configs applied to all vMX hosts, basically the username and password
- `hosts.yaml` (will be created by Mininet's Juniper vMX class into `/tmp/vmx-hosts.yaml`): actual list of vMX hosts instantiated by Mininet and their correspondent IP address
- `set-config-file.py` (which should be placed into `/opt/vmx/nornir/set-config-file.py`): nornir script which will apply the initial Juniper configuration to work with OESS

# References

- https://nornir-pyez.readthedocs.io
- https://medium.com/@sydasif78/getting-started-with-nornir-for-python-network-automation-6c23de5744af
- OESS: https://globalnoc.github.io/OESS/api/data
