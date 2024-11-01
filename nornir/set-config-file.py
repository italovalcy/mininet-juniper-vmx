import argparse
import sys
from nornir import InitNornir
from nornir_netmiko.tasks import netmiko_send_config
from nornir_netmiko.tasks import netmiko_commit
from nornir_utils.plugins.functions import print_result


parser = argparse.ArgumentParser()
parser.add_argument('config_file')
parser.add_argument('-n', '--name', help="name of the router to apply the config, if not specified will be executed on all hosts")

args = parser.parse_args()

nr = InitNornir(
    runner={
        "plugin": "threaded",
        "options": {
            "num_workers": 100,
        },
    },
    inventory={
        "plugin": "SimpleInventory",
        "options": {
            "host_file": "/tmp/vmx-hosts.yaml",
            "group_file": "/opt/vmx/nornir/vmx-group.yaml"
        },
    },
)

if args.name:
    nr = nr.filter(name=args.name)

def netmiko_send_config_from_file_exmaple(task):
    task.run(task=netmiko_send_config, config_file=args.config_file)

def netmiko_commit_exmaple(task):
    task.run(task=netmiko_commit)

results=nr.run(task=netmiko_send_config_from_file_exmaple)
print_result(results)

results=nr.run(task=netmiko_commit_exmaple)
print_result(results)
