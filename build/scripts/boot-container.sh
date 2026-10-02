#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
exec docker run --rm --name kestrel-boot-test --cpus=1 --memory=3g --memory-swap=3g --device /dev/kvm \
 -v "$PWD":/src -w /src archlinux:latest bash -euxc '
 renice 15 -p $$; ionice -c3 -p $$
 pacman -Sy --noconfirm qemu-desktop edk2-ovmf python-pillow
 bash scripts/boot-test.sh out/kestrel-os-2026.10.02-x86_64.iso 150
 '
