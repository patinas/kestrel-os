#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
exec docker run --rm --name kestrel-m2-tests --cpus=1 --memory=3g --memory-swap=3g --device /dev/kvm \
 -v "$PWD":/src -w /src archlinux:latest bash -euxc '
 renice 19 -p $$; ionice -c3 -p $$
 pacman -Sy --noconfirm qemu-desktop edk2-ovmf python-pillow libisoburn minisign
 mkdir -p out/m2-tests
 ovmf_vars=$(find /usr/share -name "OVMF_VARS*.fd" -type f | head -1)
 ovmf_code=$(find /usr/share -name "OVMF_CODE*.fd" -type f | head -1)
 [ -n "$ovmf_vars" ] && [ -n "$ovmf_code" ]
 [ -e out/m2-tests/OVMF_VARS.fd ] || cp "$ovmf_vars" out/m2-tests/OVMF_VARS.fd
 printf "%s\n" "$ovmf_code" > out/m2-tests/ovmf-code.path
 touch out/m2-tests/ready
 sleep infinity
 '
