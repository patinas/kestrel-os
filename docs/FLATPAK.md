# Flatpak on Kestrel OS

Flatpak is the only native-app install path for users (the read-only A/B
root never changes; `pacman` stays behind the Advanced toggle as a
containerised dev tool only).

What the image ships:

- `flatpak`, `xdg-desktop-portal`, `xdg-desktop-portal-gtk` and
  `xdg-desktop-portal-wlr` in `build/profile/packages.x86_64`.
- Flathub as the single allow-listed remote, preconfigured via the
  canonical `/etc/flatpak/remotes.d/flathub.flatpakrepo` drop-in fetched
  from https://flathub.org/repo/flathub.flatpakrepo (includes Flathub's
  GPG key, so installs verify out of the box).

  Scope note: the allow-list is enforced at system scope (remote changes
  there need root). Flatpak's user-scope installation lives in the user's
  own home and is theirs to control, like any file they own; a user can
  always `flatpak --user remote-add` for themselves. "Flathub only" is a
  system-scope guarantee, not a claim that the user cannot add personal
  remotes.
- `XDG_DATA_DIRS` in `kestrel-session` includes the system and user
  Flatpak exports, so Flatpak apps' desktop files and icons are visible
  to the shell. `XDG_CURRENT_DESKTOP=wlroots` selects the wlr portal for
  screencast/screenshot and the gtk portal for everything else, via the
  `/usr/share/xdg-desktop-portal/wlroots-portals.conf` drop-in shipped in the
  image (default=gtk; ScreenCast and Screenshot=wlr).
- The launcher lists Flatpak apps next to Chrome PWAs (any desktop entry
  whose Exec starts with `/usr/bin/flatpak run `).
- polkit rule `/etc/polkit-1/rules.d/50-kestrel-flatpak.rules` lets the
  desktop user (wheel) install, update and remove apps/runtimes and
  refresh metadata without a password. It is an explicit action
  allow-list (flatpak's system-helper policy action IDs), not a
  wildcard: remote add/change, bundle installs, downgrades, repo/config
  changes and overrides still demand root, so the Flathub-only remote
  allow-list cannot be widened without Advanced sudo. User-scope
  installs (`flatpak install --user ...`) need no polkit at all.
  Installs live in `/var/lib/flatpak` (system) or
  `~/.local/share/flatpak` (user); both sit on the persistent kdata
  partition (install.sh: `LABEL=kdata /var ext4`, `/var/home` bind to
  `/home`), so apps survive A/B system updates. The read-only root is
  never touched.

Installing an app today (Advanced terminal):

    flatpak install flathub org.example.App

The new app appears in the launcher the next time it opens. A graphical
software store is roadmap work; the OS support above is the foundation
it will build on.
