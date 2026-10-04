# Advanced terminal and packages (pending CI verification)

Settings has an "Enable terminal / sudo (advanced)" checkbox, off by default. Enabling opens a terminal that asks for a new local sudo password of at least 12 characters. No default password or passwordless general sudo is shipped. The password record and setting live under writable /var/lib/kestrel. Disabling revokes new sudo commands, removes the password record and closes terminal windows. Already-running root processes cannot be reliably undone by this toggle; reboot after sensitive use.

Use `sudo kestrel-packages -S package`. On live USB, pacman uses the RAM overlay: changes disappear at reboot. On installed systems, packages go into a persistent Arch development root under /var/lib/kestrel/devroot through systemd-nspawn. Packages are not installed into the immutable A/B root, and container applications are not automatically exposed as host UI shortcuts. Initial container setup needs network. A root-capable terminal can still change the system intentionally; treat this as developer access, not a sandbox guarantee.

The web bridge runs as kestrel, listens only on loopback, validates Host and Origin, requires a per-session CSRF token and rejects framing. The narrow root-owned toggle helper is the only no-password sudo command. Dedicated sudo PAM authentication uses a root-readable scrypt record and requests a password for every command. This security path is experimental until tested.

PAM mechanics: https://man.archlinux.org/man/pam_exec.8.en
Sudo policy: https://man.archlinux.org/man/sudoers.5.en
