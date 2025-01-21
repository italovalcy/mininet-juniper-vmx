FROM italovalcy/mininet:latest

LABEL org.opencontainers.image.source="https://github.com/atlanticwave-sdx/mininet-juniper-vmx"
LABEL org.opencontainers.image.authors="italovalcy@gmail.com"

# download Junos and place it on the current directory named as hda.qcow2
COPY hda.qcow2 /opt/vmx/hda.qcow2

RUN export DEBIAN_FRONTEND=noninteractive \
 && apt-get update \
 && apt-get install -y --no-install-recommends qemu-system-x86 expect netcat-openbsd python3-pip iptables \
 && rm -rf /var/lib/apt/lists/*

RUN --mount=source=.,target=/mnt,type=bind \
    cp -r /mnt/src /mnt/configs /mnt/nornir /mnt/*.py /mnt/*.sh /opt/vmx/ \
 && cd /opt/vmx \
 && python3 -m pip install -r nornir/requirements.txt \
 && python3 -m pip install --no-cache-dir .
