#!/usr/bin/env bash
set -euo pipefail
cd /src
CODE=$(cat out/m2-tests/ovmf-code.path)
[ -e out/m2-tests/full.qcow2 ] || qemu-img create -f qcow2 out/m2-tests/full.qcow2 40G
exec qemu-system-x86_64 -machine q35,accel=kvm -cpu max -m 2048 -smp 1 \
 -drive if=pflash,format=raw,readonly=on,file="$CODE" -drive if=pflash,format=raw,file=out/m2-tests/OVMF_VARS.fd \
 -drive if=none,id=testdisk,format=qcow2,file=out/m2-tests/full.qcow2 -device virtio-blk-pci,drive=testdisk,serial=KESTREL_TEST_ONLY \
 -cdrom out/kestrel-os-2026.10.02-x86_64.iso -kernel out/install-test/vmlinuz -initrd out/install-test/initramfs \
 -append 'archisobasedir=kestrel archisolabel=KESTREL_202610 console=tty0 console=ttyS0 systemd.run="/usr/bin/mkdir -p /run/kestrelshare" systemd.run="/usr/bin/mount -t 9p -o trans=virtio,version=9p2000.L,ro kestreltest /run/kestrelshare" systemd.run="/usr/bin/bash /run/kestrelshare/tests/jobs/install.sh" systemd.run_success_action=none systemd.run_failure_action=none' \
 -virtfs local,path=/src,mount_tag=kestreltest,security_model=none,readonly=on \
 -vga virtio -device virtio-net,netdev=n -netdev user,id=n -display none \
 -serial file:out/m2-tests/install.log -qmp unix:out/m2-tests/qmp.sock,server,nowait
