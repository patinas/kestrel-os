# Comparison with ChromeOS behaviour

Public help pages and documentation only. No code, assets, fonts or trademarks are copied. Status words: implemented in source (not yet run on a VM), or gap.

Sources:
- Window snap, Snap Groups: https://support.google.com/chromebook/answer/177891 and https://support.google.com/chromebook/answer/15400342
- Keyboard shortcuts and screenshots: https://support.google.com/chromebook/answer/183101 and https://support.google.com/chromebook/answer/10474268
- Shelf: https://support.google.com/chromebook/answer/3113576
- labwc options used: https://labwc.github.io/labwc-config.5.html and https://labwc.github.io/labwc-actions.5.html

| Behaviour on ChromeOS | Kestrel | Status |
|---|---|---|
| Drag to screen edge snaps a window to half | labwc edge snapping is on by default, and Alt+[ / Alt+] snap | existing; not UI-tested |
| Screenshot is saved and also copied to the clipboard | `kestrel-screenshot` now also runs `wl-copy` | implemented in source |
| Screenshot toast appears | `notify-send` had no notification daemon, so the toast was never shown | fixed: `mako` starts with the desktop |
| Virtual desks | 4 labwc workspaces: Super+] / Super+[ switch, Super+Shift+] / [ move the window | implemented in source |
| Overview of open windows (Show windows key) | Super+Tab and Ctrl+F4 open labwc's window list menu. This is a list, not live thumbnails | partial |
| Close window shortcut | Alt+F4 | implemented in source |
| Idle dim, then screen off | `kestrel-idle` (swayidle): dim at 5 min, screen off at 7 min, wake on input. Skipped on the CI test VM | implemented in source, not run in a VM |
| Lock (Search+L) | Optional lock password in Settings, off by default. Super+L, idle at 7 min and before sleep lock with swaylock only when a password is set; otherwise a notice says it is off. Scrypt hash in the user's home, mode 600. Protects the screen, not the disk | helper and bridge unit-tested (`lock-unit.sh`, `lock-bridge.sh`); swaylock/PAM path not run in a VM |
| Snap halves and quarters | Alt+[ / Alt+] toggle left/right snap (press again to restore). Super+arrows snap, and combining two arrows gives a quarter (labwc `SnapToEdge combine`) | implemented in source, not UI-tested |
| Snap Groups with shared divider and group overview | none. labwc has no grouped-resize feature | gap |
| Shelf pin/unpin by the user | Fixed launcher, mail, video, task list. Waybar takes icons from a font, so user pins would need per-app image modules and a regenerated config. That changes the measured shelf geometry, so it needs its own design and retest | gap, deliberately deferred |

Nothing here has been run in the VM or on hardware. The next UI test must check desk switching, the window list menu, the clipboard copy and that the screenshot toast appears.

## Grouped taskbar (one icon per app)

ChromeOS's shelf shows one icon per app and lists the windows when an app has several. Waybar 0.15.0 (Arch) cannot group: `squash-list` was merged on 2026-07-04, after that release. `kestrel-taskbar` fills the gap. It reads the open windows through the public wlr-foreign-toplevel-management protocol, draws one 40x40 icon per app (active pill, dimmed when minimised, count badge for 2+ windows) and Waybar shows those images. One window: click focuses it, or restores it if minimised. Several windows: click opens a list to pick from. If pywayland is missing, `kestrel-desktop` falls back to the plain per-window Waybar config. Test: `build/tests/ci/taskbar-test.py` runs the daemon against a mock compositor.
