#!/usr/bin/env bash
set -euo pipefail
cd /src
CODE=$(cat out/m2-tests/ovmf-code.path)
rm -f out/m2-tests/qmp.sock
exec qemu-system-x86_64 -machine q35,accel=kvm -cpu max -m 2048 -smp 1 \
 -drive if=pflash,format=raw,readonly=on,file="$CODE" -drive if=pflash,format=raw,file=out/m2-tests/OVMF_VARS.fd \
 -drive if=none,id=testdisk,format=qcow2,file=out/m2-tests/full.qcow2 -device virtio-blk-pci,drive=testdisk,serial=KESTREL_TEST_ONLY \
 -virtfs local,path=/src,mount_tag=kestreltest,security_model=none,readonly=on \
 -boot c -vga virtio -device virtio-net,netdev=n -netdev user,id=n -display none \
 -serial file:out/m2-tests/disk.log -qmp unix:out/m2-tests/qmp.sock,server,nowait
