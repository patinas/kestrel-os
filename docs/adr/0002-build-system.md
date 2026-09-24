# ADR 0002: Build system - mkosi

Status: accepted (2026-09-24)

## Options

- **archiso**: Arch's official tool for live ISO / netboot images
  (https://wiki.archlinux.org/title/Building_a_Live_CD). Great for live and
  installer media, but it builds live ISOs, not installable A/B system images.
- **mkosi**: systemd's image builder, wraps pacman/apt/dnf and builds disk
  images declaratively with systemd-repart
  (https://wiki.archlinux.org/title/Mkosi, https://man.archlinux.org/man/mkosi.1.en,
  https://github.com/systemd/mkosi/pull/1276).

## Decision

mkosi. Kestrel OS is image-based (read-only A/B slots, dm-verity, signed
unified kernel images, systemd-sysupdate). mkosi builds exactly those
artifacts, and it can also build the USB installer image and VM test images
from the same config. One tool for all targets, including aarch64.

archiso stays an option for a lightweight "try it live" ISO if mkosi's live
output turns out to be worse on old BIOS machines.
