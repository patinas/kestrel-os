# ARM / Raspberry Pi image plan
Status: proposed design, not implemented or verified. M1 is an x86_64 live ISO only.


Goal: same shell (cage + Chromium kiosk) on aarch64, Pi 4/5 first.

- Base: Arch Linux ARM (aarch64 generic rootfs, http://os.archlinuxarm.org/os/ArchLinuxARM-aarch64-latest.tar.gz) plus the Raspberry Pi kernel (linux-rpi) for Pi 4/5. Generic UEFI aarch64 boards use mainline `linux-aarch64` and the same layout as x86.
- Packages: same list as x86 minus intel/amd ucode, nvidia, steam (no ARM Steam; gaming mode is x86-only for now; optionally box64 later). GPU: mesa (v3d/panfrost/panthor), cage, chromium (Arch ARM ships it).
- Build: free, on u3 with qemu-user-static + binfmt (`docker run --privileged multiarch/qemu-user-static --reset -p yes`), then an aarch64 Arch container assembles the rootfs and a script makes a .img (loop device: 256M FAT boot, rootA, rootB, data - same A/B layout as x86).
- Boot: Pi firmware boots config.txt/cmdline.txt from the FAT partition; A/B via the `tryboot` mechanism (Pi 5/4 bootloader supports `tryboot_a_b`) with `root=LABEL=rootA|rootB`. 
- Test: qemu-system-aarch64 -M virt with UEFI for the generic image; Pi-specific boot only verifiable on real hardware. State this honestly in the release notes.
- Order of work: (1) generic aarch64 UEFI image boots to the shell in QEMU, (2) Pi 4/5 image, (3) real-hardware test by Andreas (needs a Pi and an SD card).
