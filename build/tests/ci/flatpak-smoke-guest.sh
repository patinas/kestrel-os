#!/bin/sh
# CI-only Flatpak runtime smoke. Injected into the disposable candidate ISO copy
# by 01-build-iso.sh (KESTREL_FLATPAK_SMOKE=1); never present in the repo profile.
# Runs as the kestrel user on a live tty. Verdict printed full-screen at the end
# for the screenshot evidence gate.
out=/tmp/flatpak-smoke.log; : > "$out"
both(){ printf '%s\n' "$*" | tee -a "$out"; }
V=PASS
both "flatpak: $(flatpak --version 2>&1)"
both '-- remotes (expect flathub, system scope, preconfigured) --'
flatpak remotes --columns=name,options 2>&1 | tee -a "$out"
flatpak remotes --columns=name,options | grep -q '^flathub' || V='FAIL remote'
both '-- session env inherited by the running labwc --'
lpid=$(pgrep -x labwc | head -1)
if [ -n "$lpid" ]; then
  tr '\0' '\n' < "/proc/$lpid/environ" | grep -E '^(XDG_DATA_DIRS|XDG_CURRENT_DESKTOP)=' | tee -a "$out"
  tr '\0' '\n' < "/proc/$lpid/environ" | grep -q '^XDG_DATA_DIRS=.*flatpak' || V='FAIL env'
else
  V='FAIL labwc'; both 'labwc not running'
fi
both '-- portal backend configs on disk --'
ls /usr/share/xdg-desktop-portal/portals/ 2>&1 | tee -a "$out"
[ -f /usr/share/xdg-desktop-portal/wlroots-portals.conf ] || V='FAIL portals'
both '-- system-scope install as kestrel (wheel polkit rule, no password) --'
if flatpak install -y flathub org.gnome.Calculator >>"$out" 2>&1; then
  both 'install: OK'
else
  V='FAIL install'; both 'install: FAILED'
fi
if [ "$V" = PASS ]; then
  both '-- launcher enumeration path (identical Gio filter to kestrel-launcher) --'
  enum=$(XDG_DATA_DIRS="$HOME/.local/share/flatpak/exports/share:/var/lib/flatpak/exports/share:/usr/local/share:/usr/share" python3 -c '
import gi
gi.require_version("Gio","2.0")
from gi.repository import Gio
hits=[a.get_id() for a in Gio.AppInfo.get_all() if a.should_show() and (a.get_commandline() or "").startswith("/usr/bin/flatpak run ")]
print("launcher-visible flatpak apps:", hits)
assert any("calculator" in h.lower() for h in hits), "calculator not visible to launcher filter"
' 2>&1) || V='FAIL launcher-enum'
  both "$enum"
  both '-- launching calculator into the running labwc session --'
  XDG_RUNTIME_DIR=/run/user/1000 WAYLAND_DISPLAY=wayland-1 flatpak run org.gnome.Calculator >>"$out" 2>&1 &
  sleep 25
fi
# Verdict into the log for the host machine gate, then full-screen for the visual gate.
both "SMOKE_RESULT=$V"
# CI-only log export. The host fetches the smoke log over a QEMU hostfwd to
# guest port 8766 (forwarded as 127.0.0.1:18766). Port 8765 is the kestrel
# lock/settings server and has no CI endpoint; serving here keeps the CI
# surface inside this CI-injected script. Started only after SMOKE_RESULT is
# written, so a fetched log always carries a verdict line.
nohup python3 -c '
from http.server import BaseHTTPRequestHandler, HTTPServer
class H(BaseHTTPRequestHandler):
    def do_GET(self):
        data = open("/tmp/flatpak-smoke.log", "rb").read()
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)
    def log_message(self, *a):
        pass
HTTPServer(("0.0.0.0", 8766), H).serve_forever()
' >/dev/null 2>&1 &
sleep 1
clear
echo "SMOKE_RESULT=$V"
echo "full log: $out"
