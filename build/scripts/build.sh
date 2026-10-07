#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p out work
exec docker run --name kestrel-iso-build --rm --privileged --cpus=1 --memory=3g --memory-swap=3g \
  -v "$PWD":/src -v "$PWD/cache":/var/cache/pacman/pkg -w /src archlinux:latest bash -euxc '
  renice 15 -p $$
  ionice -c 3 -p $$
  printf "Server = https://geo.mirror.pkgbuild.com/\$repo/os/\$arch\n" > /etc/pacman.d/mirrorlist
  pacman -Sy --noconfirm arch-install-scripts
  mapfile -t pkgs < <(grep -v "^[[:space:]]*#" /src/profile/packages.x86_64 | sed "/^[[:space:]]*$/d")
  # A git checkout carries host UID/GID; never preserve those owners into the OS.
  chown -R 0:0 /src/profile/airootfs
  mkdir -p /src/work/x86_64/airootfs
  cp -a /src/profile/airootfs/. /src/work/x86_64/airootfs/
  pacstrap -C /src/profile/pacman.conf -c -G -M /src/work/x86_64/airootfs "${pkgs[@]}" --debug > /src/package-install.log 2>&1
  touch /src/work/base._make_packages
  pacman -S --noconfirm archiso
  # Stock loader assets fill gaps, never overwrite source-controlled Kestrel entries.
  cp -an /usr/share/archiso/configs/releng/efiboot/. /src/profile/efiboot/
  grep -q "cow_spacesize=75%" /src/profile/efiboot/loader/entries/01-archiso-linux.conf
  grep -q "cow_spacesize=75%" /src/profile/efiboot/loader/entries/02-archiso-speech-linux.conf
  mkdir -p /src/profile/airootfs/etc/mkinitcpio.conf.d /src/profile/airootfs/etc/mkinitcpio.d
  mapfile -t pkgs < <(grep -v "^[[:space:]]*#" /src/profile/packages.x86_64 | sed "/^[[:space:]]*$/d")
  cp -a /src/profile/airootfs/. /src/work/x86_64/airootfs/
  chmod 755 /src/work/x86_64/airootfs/usr/local/bin/kestrel-*
  arch-chroot /src/work/x86_64/airootfs useradd -m -s /bin/bash -G wheel,video,audio,input kestrel
  arch-chroot /src/work/x86_64/airootfs passwd -d kestrel
  cp /src/profile/airootfs/etc/skel/.bash_profile /src/work/x86_64/airootfs/home/kestrel/.bash_profile
  chown 1000:1000 /src/work/x86_64/airootfs/home/kestrel/.bash_profile
  chown -R 0:0 /src/work/x86_64/airootfs/etc/sudoers.d
  chmod 750 /src/work/x86_64/airootfs/etc/sudoers.d
  arch-chroot /src/work/x86_64/airootfs visudo -c
  mkarchiso -v -w /src/work -o /src/out /src/profile
  sha256sum /src/out/*.iso > /src/out/SHA256SUMS
'
