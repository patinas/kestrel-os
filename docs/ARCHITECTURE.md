# Architecture

Status: draft for phase 2. Decisions are recorded in [adr/](adr/).

## Overview

```
+-------------------------------------------------------------+
|  Kestrel Shell (web UI: launcher, shelf, quick settings,    |
|  notifications, lock screen, setup wizard, settings app)    |
+------------------------------+------------------------------+
|  Browser session             |  Gaming session              |
|  Chromium (Wayland/Ozone)    |  gamescope + Steam + Proton  |
+------------------------------+------------------------------+
|  kestrel-compositor (wlroots): one shell, no desktop        |
+-------------------------------------------------------------+
|  System services: systemd, NetworkManager (iwd backend),    |
|  BlueZ, PipeWire + WirePlumber, UPower, fwupd,              |
|  kestrel-hwdetect                                           |
+-------------------------------------------------------------+
|  Graphics: Mesa (Intel, AMD, NVK, V3D) / nvidia-open        |
+-------------------------------------------------------------+
|  Linux kernel + split linux-firmware                        |
+-------------------------------------------------------------+
|  Read-only A/B system image, encrypted /home                |
+-------------------------------------------------------------+
```

## 1. Base: Arch Linux (x86_64), Arch Linux ARM (aarch64)

Chosen because gaming and new hardware need the newest kernel, Mesa and
NVIDIA drivers, and Arch ships them first. Arch runs on any x86_64 machine
with 512 MiB RAM and a base install is under 2 GiB
(https://wiki.archlinux.org/title/Installation_guide).

We do not expose pacman to users. Arch is the package source; Kestrel ships
a tested, versioned system image built from a pinned snapshot of the Arch
repositories, so every user runs the same combination.

Rejected:

- Chromium OS / openFyde: Portage-based build with no real NVIDIA support
  (https://fydeos.io/help/knowledge-base/installation-guides/fydeos-for-pc/fydeos-for-pc-variant/).
- Debian: older Mesa and kernel, worse for gaming and new GPUs.
- Alpine: musl libc fits poorly with Steam/Proton and NVIDIA's userspace.

See [adr/0001-base-distribution.md](adr/0001-base-distribution.md).

## 2. System model: image-based, A/B updates

- The OS is a read-only image. Two slots (A/B). Updates download into the
  unused slot with systemd-sysupdate and apply on reboot; a failed boot rolls
  back automatically. This is the ChromeOS update model.
  (https://www.freedesktop.org/software/systemd/man/latest/systemd-sysupdate.html)
- Partitions are defined declaratively with systemd-repart.
- /home is encrypted (systemd-homed or LUKS with TPM2 where present).
- User apps: web apps first; Flatpak for the few native apps we allow.

## 3. Compositor and shell

- `kestrel-compositor`: a small wlroots-based Wayland compositor. It only
  knows one shell and one layout model (full-screen windows, split view,
  overview), like ChromeOS's Ash. No desktop icons, no panels plugins, no
  theme switching.
- `kestrel-shell`: the whole UI (launcher, shelf, quick settings, lock
  screen, first-boot setup, settings) is a web UI rendered by the compositor.
  The same idea exists in https://github.com/codebam/viewport. It talks to
  system services over D-Bus through a small, permission-checked bridge.
- Why a web shell: one design system for shell and apps, fast iteration, and
  the shell looks the same on every GPU.

## 4. Browser session

- Chromium (open-source build, not Google Chrome) on Wayland via Ozone, with
  GPU rasterisation and hardware video decode (VA-API on Intel/AMD,
  NVDEC via nvidia-open where available).
- Each web app can be pinned and runs in its own window like a native app.

## 5. Gaming session

- Valve's gamescope micro-compositor as a separate session, same model as
  Steam Deck and ChimeraOS (https://github.com/ValveSoftware/gamescope/,
  https://github.com/chimeraos/gamescope-session/).
- Steam + Proton. Launched from the shell; switching back ends the session
  and frees the resources.
- On hybrid laptops, games render on the discrete GPU through PRIME offload;
  the browser session stays on the integrated GPU to save battery.

## 6. Graphics drivers

See [HARDWARE.md](HARDWARE.md).

| GPU | Driver |
|---|---|
| Intel (Gen 7+) | Mesa iris / anv, intel-media-driver |
| Intel (older) | Mesa crocus / i915, libva-intel-driver |
| AMD (GCN 1+) | amdgpu kernel driver, Mesa radeonsi / RADV |
| AMD (pre-GCN) | Mesa r600, browser session only |
| NVIDIA Turing (RTX 20 / GTX 16) and newer | nvidia-open (proprietary userspace) |
| NVIDIA Kepler to Ampere without nvidia-open | Mesa NVK (Vulkan 1.4) + Zink (OpenGL) |
| Raspberry Pi 4/5 | Mesa V3D / V3DV |

NVK supports Kepler through Ada and consumer Blackwell and needs Linux 6.6+
(https://docs.mesa3d.org/drivers/nvk.html).

## 7. Hardware detection

`kestrel-hwdetect` runs on first boot and after hardware changes:

1. Reads PCI/USB IDs and DMI data.
2. Picks the GPU driver stack, Wi-Fi driver (including Broadcom `wl` where
   needed), firmware packages, and power profile.
3. Writes the result to a machine profile. The shell shows a clear summary
   in Settings > About this device.

The logic starts from archinstall's GPU detection
(https://github.com/archlinux/archinstall/blob/master/archinstall/lib/hardware.py).

## 8. Build system: mkosi

One declarative configuration per architecture under `build/mkosi/`,
producing:

- a bootable USB installer / live image,
- A/B update images (sysupdate format),
- a VM image for testing.

See [adr/0002-build-system.md](adr/0002-build-system.md).

Image builds do not depend on GitHub Actions minutes. Images are built
locally or on a self-hosted builder.

## 9. Security and lockdown

Kestrel OS is locked down the way ChromeOS is. What that means in concrete
terms is defined in [LOCKDOWN.md](LOCKDOWN.md). In short: read-only verified
system image, no root for normal users, sandboxed browser and apps,
automatic updates with rollback, and an explicit developer mode to unlock.
