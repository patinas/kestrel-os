# Kestrel OS

An open-source browser-first OS prototype, licensed under GPL-3.0.

## Current status

The x86_64 live ISO and installed browser shell boot in QEMU. [Public CI run 4](https://github.com/patinas/kestrel-os/actions/runs/37118001480) passed the full install, signed A-to-B-to-A updates, same-process 60-second Cage/Chromium health gates, systemd blessing, corrupted-signature rejection, and fallback to healthy A after three induced unhealthy B boots. The tested source is `4ca0a57a5b51ccc6bfdc7873e2369a7988a3728a`. CI uses disposable QEMU/KVM disks and test-only signing keys; it is not a hardware or release certification.

This is a VM-tested alpha, not an OS ready for real installation. The installer requires QEMU/KVM, QEMU DMI and a virtio disk with the exact serial `KESTREL_TEST_ONLY`. Do not weaken these guards to install on a real machine.

Testing on the shared TV host stopped after two playback timeouts under VM load, including one with nice 19, idle I/O and a one-minute guard. No further VM tests are permitted on that host. Later tests ran on a free standard public GitHub Actions runner, with no artifact uploads.

The installed package list includes Steam/gamescope and GPU packages. Package presence does not prove gaming or acceleration. ARM/Pi boot, real hardware, verified root images, production lockdown and browser/network interaction remain untested. No downloadable release is published.

See [the test record](docs/TESTING.md) for observed results, failures and source-only fixes.

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
