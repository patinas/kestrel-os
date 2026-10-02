# Kestrel OS

An open-source browser-first OS prototype, licensed under GPL-3.0.

## Current status

The x86_64 live ISO boots to a Chromium/Cage shell in QEMU. The experimental installer has populated both root slots on a disposable 24 GiB qcow2 disk. A separate UEFI boot, with no ISO or external kernel/initramfs, reached the shell from default slot A.

This is a VM-tested alpha, not an OS ready for real installation. The installer refuses disks unless it detects QEMU/KVM, QEMU DMI and a virtio disk with the exact serial `KESTREL_TEST_ONLY`. Do not weaken these guards to install on a real machine.

Not verified:
- Slot B boot, signed update application, boot-count fallback or automatic rollback.
- Steam/gamescope, NVIDIA acceleration or real hardware compatibility.
- ARM/Pi boot, verified root images, production lockdown or browser/network interaction.

The live image includes gaming packages. The installed system currently installs the smaller browser package set, so live gaming packages do not prove installed gaming support. The shell footer still reads "alpha live image" on installed boots.

See [the test record](docs/TESTING.md) for evidence, constraints and reproduction notes.

## Goals

A small browser shell, broad Linux hardware support and an optional gaming session. Read-only root slots, signed updates and health-gated rollback are intended parts of the design. These goals are not claims about the current prototype.

## Documentation

- [Architecture](docs/ARCHITECTURE.md)
- [Hardware strategy](docs/HARDWARE.md)
- [Design](docs/DESIGN.md)
- [ARM proposals](docs/ARM.md)
- [Update proposal](docs/UPDATES.md)
- [Lockdown proposal](docs/LOCKDOWN.md)
- [Repository layout](docs/LAYOUT.md)
- [Roadmap](ROADMAP.md)

## License

GPL-3.0. See [LICENSE](LICENSE).
