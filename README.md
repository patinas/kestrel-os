# Kestrel OS

An open-source browser-first OS prototype, licensed under GPL-3.0.

## Current status

The x86_64 live ISO and installed browser shell boot in QEMU. [Public CI run 4](https://github.com/patinas/kestrel-os/actions/runs/37118001480) passed the full install, signed A-to-B-to-A updates, same-process 60-second Cage/Chromium health gates, systemd blessing, corrupted-signature rejection, and fallback to healthy A after three induced unhealthy B boots. The tested source is `4ca0a57a5b51ccc6bfdc7873e2369a7988a3728a`. CI uses disposable QEMU/KVM disks and test-only signing keys; it is not a hardware or release certification.

This is a VM-tested alpha, not an OS ready for real installation. The installer requires QEMU/KVM, QEMU DMI and a virtio disk with the exact serial `KESTREL_TEST_ONLY`. Do not weaken these guards to install on a real machine.

Testing on the shared TV host stopped after two playback timeouts under VM load, including one with nice 19, idle I/O and a one-minute guard. No further VM tests are permitted on that host. Later tests ran on a free standard public GitHub Actions runner, with no artifact uploads.

Current source removes Steam from the base image and adds optional installer choices (none, Lutris, Steam, both). Package presence does not prove gaming or acceleration. ARM/Pi boot, real hardware, verified root images, production lockdown and browser/network interaction remain untested. No downloadable release is published.

## Work in progress: Chrome and Settings

The current source uses Google Chrome downloaded directly from Google after local terms acceptance, rather than distributing Chrome in the ISO. A non-persistent live USB boot needs network again. Chrome/Settings [candidate 3](https://github.com/patinas/kestrel-os/actions/runs/37196394489) failed in the QMP test driver while typing a colon. The mapping was fixed; [candidate 4](https://github.com/patinas/kestrel-os/actions/runs/37199323204) finished the build/split check but failed actual Chrome setup with a full live overlay. Its green workflow status was not a desktop pass. The HTTP/process gate then caught candidate5 failing before download: the build script overwrote custom live-overlay boot parameters. That overwrite is fixed in source; the next test must prove Chrome actually starts. Earlier Chromium boot/rollback results do not prove Chrome results.

Settings source has a real network/Bluetooth/audio/battery status bar, NetworkManager and Bluetooth setup terminals, volume/mute, Chrome refresh and an advanced terminal/sudo checkbox. The checkbox starts off; enabling requires a user-chosen local sudo password. Disabling revokes new sudo commands and closes terminal windows, but cannot undo root processes already started. Reboot after sensitive use. Live package changes are RAM-only; installed package tools use a persisted development container instead of changing the read-only A/B root. These controls and the container need CI verification. Display, timezone/layout and production OS-update controls are marked unavailable until implemented. See [advanced access](docs/ADVANCED.md), [Chrome](docs/CHROME.md) and [optional launchers](docs/INSTALLER-GAMES.md).

## USB live-test guide

A new downloadable release is still held for Chrome, Settings and installer tests. Do not use an earlier Chromium ISO as proof of the current source. The steps below apply when the tested split ISO is published with its exact filenames and checksums.

1. Download every numeric `.iso.part00`, `.iso.part01` file plus `SHA256SUMS.parts` and `SHA256SUMS.iso` from the same release. Do not mix runs.
2. Verify each part against `SHA256SUMS.parts`. On Windows use PowerShell `Get-FileHash` with SHA256 for each file and compare every value. On Linux use `sha256sum -c SHA256SUMS.parts` in that folder.
3. Join part00 then part01. Windows Command Prompt: `copy /b EXACT.iso.part00+EXACT.iso.part01 EXACT.iso`. Linux: `cat EXACT.iso.part00 EXACT.iso.part01 > EXACT.iso`. Replace EXACT with the published filename. Check the joined ISO against `SHA256SUMS.iso` (PowerShell `Get-FileHash` or Linux `sha256sum -c SHA256SUMS.iso`). Hashes detect corruption; this alpha does not yet have a production release-signing guarantee.
4. Use an empty USB drive large enough for the joined ISO. Back up the USB first: flashing erases it. Disconnect unnecessary drives to reduce wrong-drive risk. In Rufus, select the intended USB and the joined ISO, then start. If asked, use DD image mode for this hybrid ISO. Do not select an internal drive.
5. Reboot using your PC's UEFI USB boot menu. This alpha does not support Legacy BIOS. Secure Boot support is not established; do not change Secure Boot or encryption settings blindly, especially on a BitLocker PC.
6. At the Chrome prompt, read Google's terms and accept only if you agree. Connect wired network first if possible. Chrome setup downloads and verifies Google's signed package. Failure or declined terms stops the desktop rather than pretending Chromium is Chrome.
7. Live-test the shell and Settings: search, each external shortcut, network, Bluetooth, audio, battery and your real graphics hardware. A VM cannot prove your Wi-Fi, Bluetooth, audio or GPU support. Non-persistent USB package/profile changes disappear on reboot.

This is USB creation and live boot, not internal-disk installation. The installer remains guarded for disposable VM disks. Do not bypass its guards. Real UI screenshots will be added after the current Chrome captures are inspected; no mockups are presented as boot evidence.

Dansk: USB-flashning sletter USB-drevet. Denne alpha er til live-test, ikke installation på din interne disk. Chrome hentes fra Google efter din egen accept og kræver netværk. Rigtig GPU, Wi-Fi og lyd skal testes på din PC.

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
