# nornir config cmd script
from nornir import InitNornir
from nornir.core.filter import F
from nornir_netmiko.tasks import netmiko_send_config
from nornir_utils.plugins.functions import print_result


nr = InitNornir(config_file="config.yaml")
#nr = nr.filter(hostname="172.16.10.12")
nr = nr.filter(F(platform__eq="junos"))
results = nr.run(task=netmiko_send_config, config_commands=["set routing-options autonomous-system 65000"])
print_result(results)
