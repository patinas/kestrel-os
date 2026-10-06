# Kestrel UI test plan (buttons, interactions, symmetry)

Run on a 1280x800 frame in the live ISO guest. Each row needs a frame (JPEG) showing the result. A row is PASS only with a frame or log line proving it; anything not run is NOT TESTED. Geometry rules are checked by `symmetry_check.py` from measured rects.

## Control inventory (from source, b6c38ed)
Shelf (Waybar, 48 px, 8 px margins): launcher button, Mail, Video, taskbar (click = activate, middle = close, tooltip = title), Wi-Fi/Wired/Offline (click opens quick settings), volume % / Muted (click quick settings), battery %, clock (click quick settings, tooltip "Quick settings").
Launcher (kestrel-launcher, 640x480): search field (56 px, type filters, clears), app tiles (Browser, Mail, Video, Games/others, Chrome-created apps), Escape closes, tile click launches and closes.
Quick settings (360 wide): Network tile, Bluetooth tile (no adapter shows tooltip, adapter present opens kestrel-bluetooth), network status line, volume line, Mute button, volume slider, battery line, brightness line, All settings button (also Enter), Close button.
Settings (#settings page in kestrel-browser): audio buttons (volume up/down/mute), network and Bluetooth setup terminals, Chrome refresh, advanced terminal/sudo checkbox (default off), Close.
Window: titlebar buttons (minimize, maximize/restore, close), drag, resize edges, snap left/right (Alt+[ and Alt+]), Alt+- minimize, Alt+= maximize, Alt+Tab.
Keyboard: Super (on release) launcher, Super+Space launcher, Super+Return terminal, Super+B browser, Alt+Shift+S quick settings, Ctrl+F5 screenshot, Ctrl+Shift+F5 region, media keys (volume, mute, play, next, prev, brightness).

## Interaction checks for every button
hover (background change visible), pressed state, keyboard focus ring (Tab), click effect, tooltip where defined, Escape/Close dismiss, reopening works, no leftover windows, no blank page after Close.

## Symmetry/polish rules (symmetry_check.py, tolerance 1 px)
shelf left gutter == right gutter == bottom gutter; shelf centered; shelf icons same size, equal gaps, vertically centered; panel and launcher gap above shelf == shelf side gutter; panel right gutter == shelf right gutter; panel width 360; launcher left edge == shelf left edge; tiles same size with equal pitch; tile block left inset == right inset inside its container; labels left-aligned; shelf/panel dimensions on the 8 px grid.

## Findings from reading the source (before any frame was measured; verify in frames)
1. Quick settings title label had an extra 8 px left margin versus other labels and the tiles. Removed in this patch (labels now align to the tile edge).
2. Launcher FlowBox had no horizontal alignment, so four 96 px tiles would sit left of centre with free space on the right. Patch centres the grid; verify the inset rule on a frame.
3. Quick settings tiles: 8 border + 168 + 8 gap + 168 + 8 border = 360, so left and right insets are equal by construction. Mute (56x48) next to the slider and the 48 px full-width buttons are different heights from the 64 px tiles; decide if that is intended.
4. Waybar center group (Mail, Video, taskbar) is centred in the remaining space, which is not the screen centre when left and right groups differ in width. Check with the shelf-centered rule on a frame.
