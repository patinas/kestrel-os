# Kestrel OS

An open-source browser-first OS prototype, licensed under GPL-3.0.

## Current status

The x86_64 live ISO and installed browser shell boot in QEMU. The revised installer populated full-package root slots on a disposable 40 GiB disk. Installed A passed a 60-second same-process browser/compositor health gate and systemd-bless-boot removed its boot counter. A test-key signed update was written to B; B only booted successfully after a live rescue repair of missing runtime directories and executable modes. Repaired B also passed health/blessing.

This is a VM-tested alpha, not an OS ready for real installation. The installer requires QEMU/KVM, QEMU DMI and a virtio disk with the exact serial `KESTREL_TEST_ONLY`. Do not weaken these guards to install on a real machine.

The corrected end-to-end signed-update path and automatic rollback are not verified. Testing on the shared TV host stopped after two playback timeouts under VM load, including one with nice 19, idle I/O and a one-minute guard. No further VM tests are permitted on that host.

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
