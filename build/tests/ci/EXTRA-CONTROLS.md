# Extra disposable-VM controls

`extra-controls.py` runs inside the existing QMP/CDP control test. Each section records a FAIL on exceptions and continues to the next section. These are tests to run, not claims of passing behavior.

The browser workflow injects `guest-ui-probe.py` into its build copy only. The tracked OS profile has no probe, service or extra listener. The service requires the existing named CI virtio port. Port 8766 is forwarded to host loopback only. POST requests carrying browser Origin/Sec-Fetch-Site headers are rejected. The observer reports process counts, terminal-enabled/password-file presence and test results. It never returns password content or hashes.

The password is random per run. QMP types it only after OCR confirms the getpass prompt, then after the repeat prompt. It is never printed. Correct/incorrect sudo checks use stdin. Cleanup invokes the real disable helper even on failure. Prompt frames contain no echoed password. This tests a disposable local VM account only.

New checks:
- Shelf launcher and clock clicks produce the visible launcher and Quick settings panel.
- Quick Close removes the panel; Network click launches a process and visible no-adapter window.
- Filtered Browser/Mail/Video/Settings/Terminal tiles launch the right browser destination and dismiss the launcher. Locked Terminal routes to Settings, as the current implementation specifies.
- Settings Network/Bluetooth launch a process and show visible adapter messages; closing returns to Settings.
- Minimize followed by shelf activation restores the original browser target.
- Advanced UI password setup, correct/wrong sudo, terminal opening, disable and revocation.
- Temporary-key signed fixture verification and real updater rejection of a tampered signature before entry changes.
- Chrome PWA subsystem installation of a local fixture, standalone launch, Kestrel launcher discovery and mouse relaunch. Browser-menu installation is still unverified. The fixture is uninstalled afterward.

The installed sequence in `jobs/ci.sh` already tests signed A/B updates and signature tampering. This patch adds payload tampering rejection there. The browser live-VM test does not claim an A/B write or reboot.

OCR assertions were checked against the published Network/Bluetooth frames. Launcher colour detection was checked against open and filtered launcher frames. Actual mouse effects, interactive password flow and PWA behavior require CI execution.

Remaining unsupported scopes stay UNVERIFIED: installer selection UI, physical brightness/touchpad/lid/lock-on-wake, MPRIS playback, Chrome sync/keyring, production update UI/key/server, disabled gaming and Chrome-refresh UI, and human PWA installation. Shelf custom-module pressed styling remains UNMEASURED. Taskbar/titlebar state checks reference their actual control-test outcomes rather than blanket UNMEASURED labels.

Retest9: panel steps are isolated and independently caught. Launcher search/tile selection uses OCR labels and an explicit entry click, with the typed query verified in pixels before any tile click. Minimize uses the real titlebar glyph and disappearance/reappearance of the target's Settings card, not CDP's iconified state. Advanced confirmation is handled by arming Page events, clicking through QMP, waiting for javascriptDialogOpening on the same socket, then accepting. The live signature probe invokes the actual updater script because the convenience bin symlink exists only after installation. Probe exceptions return bounded error details and journal diagnostics. PWA commands use a separate browser-endpoint connection with a 25-second limit, and do not replay installs on timeout.

Retest10: whole-frame query OCR failed even with all five correct filtered tiles visible. The test now checks nonempty search-entry pixels plus the single exact requested tile label; the label fixtures pass for all five retest9 frames. Advanced click is transformed from DOM viewport to screen coordinates using the Settings card's observed pixels and DOM rect, rather than omitting browser chrome. The unsupported PWA.install API is replaced by the real browser menu path, with screenshot/OCR checks at every menu/dialog step. This path still needs CI execution. Launcher app and window rule explicitly unmaximize and resize to its intended 640x480; geometry still needs new pixel proof.

Retest11: root ownership is normalized before the checkout overlay enters the ISO work root. sudoers.d is explicitly root-owned in profile permissions and the installer resets copied sudoers/PAM ownership. visudo validates the build root. The guest observer reports those path owners without changing them. Mail launch accepts the observed signed-out workspace.google.com Gmail page, but does not claim mailbox access. PWA uses the visible address-bar Install button (cropped OCR at 3x) rather than an off-screen browser-menu item. Launcher compositing differences remain unresolved and require separate pixel verification.
