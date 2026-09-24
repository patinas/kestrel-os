# ARM and Raspberry Pi

Kestrel OS targets ARM64 (aarch64) as well as x86_64. ARM needs a different
base and boot path, so it is its own build target.

## Base

- **Arch Linux ARM** (community port of Arch, https://archlinuxarm.org) as
  the package source, so the same packages and versions as x86_64 wherever
  possible.
- Raspberry Pi 4/5 use the Raspberry Pi kernel (`linux-rpi`, from
  https://github.com/raspberrypi/linux), packaged by Arch Linux ARM
  (https://github.com/archlinuxarm/PKGBUILDs/blob/master/core/linux-rpi-16k/PKGBUILD).
  The generic `linux-aarch64` kernel also boots on Pi 5 with extra packages
  (https://github.com/archlinuxarm/PKGBUILDs/commit/33892c7421af3224fad6c602c7ad7ad66a8529d1)
  and stays as the kernel for other ARM64 boards.
- Alternative considered: Raspberry Pi OS (Debian). Better Pi-specific
  tuning, but a second package base with older Mesa. Only if Arch Linux ARM
  can't reach the polish bar on Pi.

## Boot

- Raspberry Pi: the Pi firmware bootloader (`raspberrypi-bootloader`) loads the kernel
  from the FAT boot partition. A/B slots are switched with the
  Pi's `tryboot` mechanism instead of systemd-boot.
- Other ARM64 boards with UEFI (for example via EDK2 or U-Boot's EFI): same
  systemd-boot path as x86_64.

## Graphics

- Raspberry Pi 4/5: Mesa V3D (OpenGL ES 3.1) and V3DV (Vulkan)
  (https://docs.mesa3d.org/drivers/v3d.html). Browser session with GPU
  acceleration.

## Gaming on ARM

- Best effort. Steam is x86-only; it can run on ARM64 through the FEX
  x86 emulator (https://github.com/FEX-Emu/FEX). Canonical ships a stable
  ARM64 Steam snap built this way
  (https://discourse.ubuntu.com/t/canonical-s-steam-snap-is-now-stable-on-arm64/83664).
- On Raspberry Pi, expect light and older games only. The gaming mode is
  shown only when hwdetect finds a GPU that can handle it.

## Images

- `kestrel-os-<version>-aarch64-rpi.img` - Raspberry Pi 4/5 SD/USB image.
- `kestrel-os-<version>-aarch64-uefi.img` - generic ARM64 UEFI image (later).
