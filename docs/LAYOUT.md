# Repository layout

```
kestrel-os/
  build/mkosi/        mkosi configs (shared + x86_64 + aarch64)
  compositor/         kestrel-compositor (wlroots, C)
  shell/              kestrel-shell web UI (launcher, shelf, settings, setup)
  session/browser/    Chromium session unit, flags, sandbox profile
  session/gaming/     gamescope + Steam session
  hwdetect/           kestrel-hwdetect (driver + firmware selection)
  packages/           package lists per image and per hardware group
  design/             design tokens, icons, fonts, UI guidelines assets
  docs/               architecture, hardware, lockdown, ARM, ADRs
```
