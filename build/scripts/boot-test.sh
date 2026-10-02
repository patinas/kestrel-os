#!/usr/bin/env bash
# Boot the ISO in QEMU (UEFI, no KVM needed), wait, capture a screenshot via QMP.
# Usage: scripts/boot-test.sh [iso] [wait_seconds]   -> out/boot.png
set -euo pipefail
cd "$(dirname "$0")/.."
ISO=${1:-$(ls -t out/*.iso | head -1)}; WAIT=${2:-120}
OVMF=$(find /usr/share -name "OVMF_CODE*.fd" -type f | head -1)
ACCEL=tcg; [ -w /dev/kvm ] && ACCEL=kvm
rm -f out/qmp.sock out/boot.ppm out/boot.png
qemu-system-x86_64 -machine q35,accel=$ACCEL -cpu max -m 2048 -smp 1 \
  -drive if=pflash,format=raw,readonly=on,file="$OVMF" \
  -cdrom "$ISO" -boot d -vga virtio -device virtio-net,netdev=n -netdev user,id=n \
  -display none -qmp unix:out/qmp.sock,server,nowait &
Q=$!
sleep "$WAIT"
python3 - <<'PY'
import socket,json,os
s=socket.socket(socket.AF_UNIX);s.connect("out/qmp.sock");f=s.makefile("rw")
f.readline();f.write(json.dumps({"execute":"qmp_capabilities"})+"\n");f.flush();f.readline()
f.write(json.dumps({"execute":"screendump","arguments":{"filename":os.path.abspath("out/boot.ppm")}})+"\n");f.flush();print(f.readline())
PY
kill $Q || true
if command -v convert >/dev/null; then convert out/boot.ppm out/boot.png; else python3 -c "
from PIL import Image;Image.open('out/boot.ppm').save('out/boot.png')"; fi
ls -l out/boot.png
