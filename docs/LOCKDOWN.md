# Lockdown: what "locked down like ChromeOS" means in Kestrel OS

Goal: a normal user can not break the system, and malware can not survive a
reboot. Advanced users can unlock it on purpose, with a clear warning.

## Normal mode (default)

1. **Read-only system.** The OS lives on a read-only A/B image. Nothing a
   user or app does can change it. Only the updater writes to the unused slot.
2. **Verified boot.** Signed unified kernel images and dm-verity on the
   system image. With Secure Boot enrolled, a modified image does not boot;
   without Secure Boot, verity still detects changes and falls back to the
   other slot. (ChromeOS Flex also lacks hardware-backed verified boot on
   most PCs, so this is on par or better.)
3. **No root for users.** User accounts are not in `wheel`/`sudo`. There is no
   terminal in normal mode. System settings go through the shell's settings
   app, which calls a small D-Bus service that only exposes allowed actions
   (Wi-Fi, Bluetooth, display, users, updates, power).
4. **Sandboxed browser.** Chromium's own sandbox (namespaces + seccomp), plus a
   systemd service unit with limited filesystem access (only the user's home
   directory and downloads).
5. **Sandboxed apps.** Native apps come only as Flatpaks from an allow-listed
   remote, with portals for files, camera and screen sharing. No pacman for
   users.
6. **Automatic updates.** systemd-sysupdate downloads into the other slot in
   the background. Reboot applies it. A failed boot rolls back automatically.
   Updates can't be turned off in normal mode, only postponed.
7. **Encrypted home.** Each user's data is encrypted, with the key bound to TPM2
   where present and to the login password.
8. **Powerwash.** One action in settings (or a key combination at boot) wipes
   user data and returns the device to setup. The system image is not touched.
9. **Gaming mode stays inside the rules.** Steam and games run as the user,
   inside the sandbox, with no root and no writes to the system.

## Developer mode (opt-in)

Like ChromeOS developer mode:

- Turned on from the boot menu, with a full-screen warning, and it wipes user data
  (so a thief can't use it to read an existing user's files).
- Gives a terminal, a root shell, and a writable overlay on top of the
  system image (systemd-sysext), so the base image stays verifiable.
- A persistent banner shows that the device is in developer mode.
- Turning it off wipes user data again and restores normal mode.

## Managed mode (later)

Policy file for schools and companies: allowed websites/apps, forced
extensions, disabled developer mode, update channel. Not in v1.

## What we do NOT lock down

- The user's own data and web apps.
- Choice of browser extensions (unless managed mode says otherwise).
- Hardware choice: lockdown must never make hardware support worse.
