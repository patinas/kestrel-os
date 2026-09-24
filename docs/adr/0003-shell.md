# ADR 0003: One shell, web-based, on our own wlroots compositor

Status: accepted (2026-09-24)

## Decision

A single shell (`kestrel-shell`) written as a web UI, running on a small
wlroots compositor (`kestrel-compositor`). No desktop environment, no
alternative shells, no theming engine.

## Reasons

- Polish is a requirement. One shell + one design system is the only way to
  control every pixel, like ChromeOS's Ash.
- The web UI uses the same rendering and design tokens as the rest of the
  system, and it's fast to iterate on.
- Prior art: https://github.com/codebam/viewport (Wayland compositor whose
  shell is a web page).

## Rejected

- Using GNOME/KDE with a theme: too much surface to polish, desktop clutter.
- Chromium's own Ash/ChromeOS shell: tied to the Chromium OS build.
