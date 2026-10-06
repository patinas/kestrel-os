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

## Automation
build/tests/ci/ui-states-evidence.py (run by 08-browser-ui-test.sh) drives hover, pressed (cancelled before release), Tab focus, Close/Escape dismiss, reopen, search filtering and media keys through QMP, measures rects from the real 1280x800 screendumps by CSS colour, and runs symmetry_check.py. Frames are ui-st-*.jpg in the log. UNMEASURED means the colour was not found: it is not a pass. Not automated: brightness and play/next keys (no hardware), taskbar clicks, titlebar mouse clicks, Quick Network tile launch.

## Findings from reading the source (before any frame was measured; verify in frames)
1. Quick settings title label had an extra 8 px left margin versus other labels and the tiles. Removed in this patch (labels now align to the tile edge).
2. Launcher FlowBox had no horizontal alignment, so four 96 px tiles would sit left of centre with free space on the right. Patch centres the grid; verify the inset rule on a frame.
3. Quick settings tiles: 8 border + 168 + 8 gap + 168 + 8 border = 360, so left and right insets are equal by construction. Mute (56x48) next to the slider and the 48 px full-width buttons are different heights from the 64 px tiles; decide if that is intended.
4. Waybar center group (Mail, Video, taskbar) is centred in the remaining space, which is not the screen centre when left and right groups differ in width. Check with the shelf-centered rule on a frame.

## Retest 1 changes (after run 37536965895: 52 PASS / 15 FAIL)
Fixed in the UI: Escape closes Quick settings; All settings no longer depends on Popen succeeding before close (errors are logged, close runs on idle); Quick settings shows clean labelled rows (Network, Volume, Battery, Brightness) on one left edge; Mute is 168x48 in the tile column beside a 168 px slider so every row shares the 8..352 edges; Quick settings and the launcher are borderless (no titlebar); the launcher is centred horizontally 8 px above the shelf; the launcher grid centres every row (short last row too) and all tiles reserve two label lines, so they are one size; shelf icons and pills are 40x40 / 40 px high with no glyph-width-dependent widths.
Fixed in the tests: state checks are relative (idle > hover > pressed brightness at a point away from the pointer, because screendumps draw the pointer); launcher tiles are found as non-background blocks below the search pill; the search field is clicked before typing (a previous cancelled press had moved focus to a tile, which is why typing did nothing); shelf elements are split into left, centre and right groups; the 8 px grid check allows +-2 px anti-aliasing; the old coordinate clicks in window-controls-evidence.py now use positions measured from the real frame.
Added (owner report "icons on the bar are not centred"): every shelf element 40 px tall and vertically centred in the 48 px shelf (+-1); all icon buttons one size; centre group centred on the screen (+-2) with no windows and with a window open; equal gaps inside each group; left margin == right margin; glyph/text centred inside its own pill (+-2 px both axes).
Rendered locally under Xvfb with real GTK: Quick settings and the launcher layouts and the colour measurement. NOT rendered locally: Waybar, labwc window rules (no titlebar, launcher placement), pointer states. Those are first exercised by the next CI run.

## Retest 2 changes (after run 37540642050: 79 PASS / 11 FAIL)
- Shelf glyphs: the icon font had every glyph left-aligned in a 1000-unit advance and about 85 units above the line middle (measured offsets -5/-2.5 px). build/scripts/center-icon-glyphs.py centres each glyph on its advance box and on the line middle; icons.ttf is regenerated with it (idempotent).
- Settings page: same labelled rows as Quick settings, % volume, clean network line, 640 px card, 8 px spacing grid. Checked in headless Chrome here against a fake /status.
- Tests: pass/fail uses bool(), the panel detector requires a 360 px wide panel (the Settings page has the same colour), shelf elements are measured over the full shelf width in rows 4..44, the first control script waits until the panel is on screen before clicking (the previous click landed on Chrome while the panel was still starting, so Settings never opened and control-results.json was never written), and a crash traceback is now included in the published log excerpt.
- Known limitation, reported as UNMEASURED with the reason: Waybar custom modules (launcher, mail, video) are GTK event boxes and never show :active, so there is no pressed style there.

## Retest 3 changes
- Active taskbar button (owner: "shadow not centred around icon"): measured on the retest2 frame, the 32 px app icon sat 3-4 px up and left of its 40 px highlight, so the highlight showed as a crescent on the right and bottom. Cause: min-width/min-height 40 made the button larger than its content and Waybar does not centre the content. Now the button has no min size and 4 px padding, so the highlight is the icon plus 4 px on every side by construction; the theme's default button shadows are reset. A test measures icon box against highlight (+-1 px), highlight size/centring, and any halo outside the highlight.
- Detector: shelf pills are measured at the vertical middle band (rounded caps are square there). Quick-panel detector uses row/column counts. Settings: Bluetooth shows "No Bluetooth adapter detected" alone (the extra "Not available" came from the connections command). window-controls-evidence.py: reuses an already-open panel, retries opening, records FAIL instead of crashing, falls back to opening Settings directly; adds Settings alignment checks with top/middle/bottom scroll frames, mouse titlebar maximize/restore and taskbar middle-click close.
- Pressed feedback on launcher/mail/video: not changed. Waybar custom modules cannot show :active; making them real buttons needs a different shelf implementation (own GTK shelf), not a CSS change.
