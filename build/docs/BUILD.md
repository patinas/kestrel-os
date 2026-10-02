# Kestrel alpha live image

M1: x86_64 UEFI live ISO with Cage and Chromium. QEMU/KVM boot reached the browser start page on October 2, 2026. Real hardware, GPU acceleration, launcher navigation and network functions have not been tested.

Run `build/scripts/build.sh` from Linux with Docker. It uses a privileged Arch build container with one CPU and 3 GiB RAM, low CPU/I/O priority, and disk-backed work/cache directories. Do not use this on a host without enough free disk space. The container mounts only the build directory and package cache. Package signatures remain required.

Run `build/scripts/boot-container.sh` with /dev/kvm available. QEMU and OVMF are installed only in its container. The guest has 2 GiB RAM; screenshots appear in build/out/boot.png. The live user has no password, for this disposable live image only. Do not deploy it as a secure installed workstation.

Outputs and package/work caches are ignored by git. The ISO is under build/out/ and SHA256SUMS records its hash. Installer, A/B updates, dedicated NVIDIA/gaming mode and ARM/Pi remain future work.
