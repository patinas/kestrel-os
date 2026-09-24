# Kestrel OS

A minimal, polished, browser-first operating system for any PC - old or new -
with native discrete-GPU support, so the same machine can also play games.

Kestrel OS is open source (GPL-3.0) and in early design. Nothing here is ready
to install yet.

## Why

ChromeOS Flex showed that a browser-first OS can bring old computers back to
life. But it has hard limits:

- Google only guarantees it on certified models, and it runs on Intel/AMD PCs
  only - no ARM.
- Open Chromium OS forks such as FydeOS officially do not support NVIDIA
  graphics; the advice is to turn the discrete GPU off.
- There is no real gaming story.

Kestrel OS keeps what makes ChromeOS good - one clean shell, automatic safe
updates, fast boot, nothing to maintain - and removes those limits.

## What makes it different from ChromeOS Flex

| | ChromeOS Flex | Kestrel OS |
|---|---|---|
| License | Proprietary | GPL-3.0 |
| CPUs | Intel/AMD x86_64 | x86_64 and ARM64 (Raspberry Pi 4/5 and others) |
| NVIDIA GPUs | Not a goal | First-class: `nvidia-open` + Mesa NVK fallback |
| AMD / Intel GPUs | Yes | Yes, latest Mesa |
| Gaming | No | Separate Steam + Proton mode on Valve's gamescope |
| Hardware | Certified list | As wide as Linux itself: all common Wi-Fi, Bluetooth, audio and GPU hardware, auto-detected |
| Updates | A/B, automatic | A/B, automatic (systemd-sysupdate) |
| Lockdown | Read-only, verified, no root | Same model: read-only verified image, no root, sandboxed apps, opt-in developer mode |

## Principles

1. **Polish is a requirement, not a nice-to-have.** One shell, one design
   system, no desktop clutter. If a feature can't be made to look and feel
   finished, it doesn't ship.
2. **Works on anything.** Target: a 10-year-old PC with 2 GB RAM runs the
   browser session smoothly.
3. **Hardware just works.** Wi-Fi, Bluetooth, audio, GPU, touchpad and
   suspend are detected and set up on first boot. No terminal needed.
4. **Games when you want them.** The gaming mode only uses resources while it
   runs.
5. **Nothing to maintain.** Read-only system image, automatic A/B updates,
   instant rollback.

## Documentation

- [Architecture](docs/ARCHITECTURE.md)
- [Hardware support strategy](docs/HARDWARE.md)
- [Design system and polish rules](docs/DESIGN.md)
- [ARM and Raspberry Pi](docs/ARM.md)
- [Architecture decisions](docs/adr/)
- [Lockdown (ChromeOS-style)](docs/LOCKDOWN.md)
- [Repository layout](docs/LAYOUT.md)

## Status

Phase 1 (research) is done. Phase 2 (foundations) has started: architecture,
build-system decision and repository layout. First bootable image is the next
milestone - see [ROADMAP.md](ROADMAP.md).

## License

GPL-3.0. See [LICENSE](LICENSE).
