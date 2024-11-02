FROM italovalcy/mininet:latest

LABEL org.opencontainers.image.source="https://github.com/atlanticwave-sdx/mininet-juniper-vmx"
LABEL org.opencontainers.image.authors="italovalcy@gmail.com"

RUN export DEBIAN_FRONTEND=noninteractive \
 && apt-get update \
 && apt-get install -y --no-install-recommends qemu-system-x86 expect netcat-openbsd python3-pip iptables \
 && rm -rf /var/lib/apt/lists/*

COPY . /opt/vmx

RUN cd /opt/vmx \
 && test -f ./hda.qcow2 || ( echo "\n\n\n\t>>> Missing Junos image 'hda.qcow2'! See README.md.\n\n\n" && exit 1 )\
 && python3 -m pip install -r nornir/requirements.txt \
 && python3 -m pip install --no-cache-dir .
