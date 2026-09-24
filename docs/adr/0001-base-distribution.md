# ADR 0001: Base distribution

Status: accepted (2026-09-24)

## Decision

Arch Linux on x86_64, Arch Linux ARM on aarch64, both as package sources
behind a Kestrel-built, versioned, read-only image.

## Reasons

- Needs the newest kernel, Mesa and NVIDIA drivers for gaming and new hardware.
- Very small base (512 MiB RAM minimum, under 2 GiB install:
  https://wiki.archlinux.org/title/Installation_guide).
- Existing GPU detection logic in archinstall to start from.

## Rejected

- Chromium OS / openFyde: Portage build, NVIDIA not supported
  (https://fydeos.io/help/knowledge-base/installation-guides/fydeos-for-pc/fydeos-for-pc-variant/).
- Debian / Ubuntu: older graphics stack.
- Alpine: musl libc, poor fit for Steam/Proton and NVIDIA userspace.

## Risk

Rolling release can break things. We pin a snapshot of the Arch repositories
per release and only ship images that pass the hardware test matrix.
