FROM italovalcy/mininet:latest

COPY hda.qcow2 /opt/vmx/hda.qcow2

RUN --mount=source=.,target=/mnt,type=bind \
    export DEBIAN_FRONTEND=noninteractive \
 && apt-get update \
 && apt-get install -y qemu-system-x86 expect netcat-openbsd python3-pip iptables \
 && python3 -m pip install -r /mnt/nornir/requirements.txt \
 && cp -r /mnt/nornir /opt/vmx/ \
 && cp /mnt/juniper_vmx.py /usr/local/lib/python3.11/dist-packages/mininet/juniper_vmx.py \
 && cp /mnt/setup-basic-vmx.sh /opt/vmx/setup-basic-vmx.sh \
 && cp /mnt/setup-mgmt-vmx.sh /opt/vmx/setup-mgmt-vmx.sh \
 && cp /mnt/cleanup-mgmt-vmx.sh /opt/vmx/cleanup-mgmt-vmx.sh \
 && rm -rf /var/lib/apt/lists/*
