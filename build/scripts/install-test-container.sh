#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
exec docker run --rm --name kestrel-install-test --cpus=1 --memory=3g --memory-swap=3g --device /dev/kvm \
 -v "$PWD":/src -w /src archlinux:latest bash -euxc '
 renice 15 -p $$; ionice -c3 -p $$
 pacman -Sy --noconfirm qemu-desktop edk2-ovmf python-pillow libisoburn
 mkdir -p out/install-test
 xorriso -osirrox on -indev out/kestrel-os-2026.10.02-x86_64.iso -extract /kestrel/boot/x86_64/vmlinuz-linux out/install-test/vmlinuz
 xorriso -osirrox on -indev out/kestrel-os-2026.10.02-x86_64.iso -extract /kestrel/boot/x86_64/initramfs-linux.img out/install-test/initramfs
 [ -e out/install-test/blank.qcow2 ] || qemu-img create -f qcow2 out/install-test/blank.qcow2 24G
 ovmf=$(find /usr/share -name "OVMF_CODE*.fd" -type f | head -1)
 timeout 1500 qemu-system-x86_64 -machine q35,accel=kvm -cpu max -m 2048 -smp 1 \
 -drive if=pflash,format=raw,readonly=on,file="$ovmf" \
 -drive if=none,id=testdisk,format=qcow2,file=out/install-test/blank.qcow2 -device virtio-blk-pci,drive=testdisk,serial=KESTREL_TEST_ONLY \
 -cdrom out/kestrel-os-2026.10.02-x86_64.iso -kernel out/install-test/vmlinuz -initrd out/install-test/initramfs \
 -append "archisobasedir=kestrel archisolabel=KESTREL_202610 console=tty0 console=ttyS0 kestrel.install-test" \
 -vga virtio -device virtio-net,netdev=n -netdev user,id=n -display none \
 -serial file:out/install-test/serial.log -qmp unix:out/install-test/qmp.sock,server,nowait
 '
