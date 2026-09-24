# Hardware support strategy

Requirement: as much hardware as possible works out of the box - Wi-Fi,
Bluetooth, audio, GPUs (AMD, Intel, NVIDIA), touchpads, webcams, suspend.

## Kernel

- Latest stable kernel on x86_64 (Arch `linux`), with an LTS kernel as
  a second boot option for problem machines.
- The Raspberry Pi kernel on Pi hardware (see [ARM.md](ARM.md)).

## Firmware

`linux-firmware` is over 700 MB raw
(https://github.com/NixOS/nixpkgs/issues/148197), too large for low-end
installs. Approach, like Fedora's firmware split
(https://www.fedoraproject.org/wiki/Changes/Linux_Firmware_Minimization):

- Installer/live image: all firmware, generic initramfs, so every machine can
  boot and get online.
- Installed system: `kestrel-hwdetect` keeps only the firmware groups the
  machine needs (for example Intel Wi-Fi, AMD GPU, Realtek Bluetooth), and
  re-runs when new hardware appears.

## Graphics

| Vendor | Stack | Notes |
|---|---|---|
| AMD | amdgpu + Mesa radeonsi/RADV, VA-API | Best-supported gaming GPU on Linux. GCN 1/2 cards use amdgpu, not radeon. |
| Intel | Mesa iris/anv (or crocus for old chips), intel-media-driver / libva-intel-driver | |
| NVIDIA Turing and newer | nvidia-open kernel modules + NVIDIA userspace | Default for RTX 20 / GTX 16 and newer. |
| NVIDIA Kepler to Ampere (fallback) | Mesa NVK + Zink | Open Vulkan 1.4 driver, needs Linux 6.6+ (https://docs.mesa3d.org/drivers/nvk.html) |
| Hybrid laptops | PRIME render offload | Shell on iGPU, games on dGPU. |

## Wi-Fi

- NetworkManager with the iwd backend (small, fast, from Intel):
  https://wiki.archlinux.org/title/Iwd, https://wiki.archlinux.org/title/NetworkManager
- Intel, Realtek, MediaTek, Qualcomm/Atheros: in-kernel drivers + linux-firmware.
- Broadcom: in-kernel brcmfmac/b43 where they work; the proprietary `wl`
  driver (broadcom-wl) for chips that need it, picked by hwdetect
  (https://wiki.archlinux.org/title/Broadcom_wireless). Some old `wl` chips
  lack newer handshakes, so the setup wizard warns about captive portals there.

## Bluetooth and audio

- BlueZ 5 + PipeWire/WirePlumber. PipeWire has Bluetooth audio enabled by
  default and handles A2DP and headset profiles
  (https://wiki.archlinux.org/title/Bluetooth,
  https://wiki.archlinux.org/title/Bluetooth_Headset).
- SOF firmware for modern Intel laptop audio.

## Other

- libinput for touchpads and touchscreens, iio-sensor-proxy for rotation.
- fwupd for firmware updates where vendors publish them.
- power-profiles-daemon + UPower for battery life.

## Hardware test matrix

We keep a public list of tested machines (like ChromeOS Flex's certified
list, but open): model, CPU, GPU, Wi-Fi, Bluetooth, audio, suspend, result.
