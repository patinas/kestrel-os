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
| Idle dim, screen off, lock on lid close | none | gap |
| Snap Groups with shared divider | none | gap |
| Shelf pin/unpin by the user | Fixed launcher, mail, video, task list | gap |

Nothing here has been run in the VM or on hardware. The next UI test must check desk switching, the window list menu, the clipboard copy and that the screenshot toast appears.
