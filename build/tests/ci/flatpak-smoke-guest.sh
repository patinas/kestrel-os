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
  # Env comes from the compositor itself, never a guessed fallback: run
  # 40461708408 proved hardcoded XDG_RUNTIME_DIR=/run/user/1000
  # WAYLAND_DISPLAY=wayland-1 wrong for this labwc session (Gtk-WARNING:
  # Failed to open display, no window in the app screenshot for the third
  # run in a row).
  LW=$(tr '\0' '\n' < "/proc/$lpid/environ" | sed -n 's/^WAYLAND_DISPLAY=//p' | head -1)
  LX=$(tr '\0' '\n' < "/proc/$lpid/environ" | sed -n 's/^XDG_RUNTIME_DIR=//p' | head -1)
  both "labwc exec env: WAYLAND_DISPLAY=${LW:-unset} XDG_RUNTIME_DIR=${LX:-unset}"
  # /proc/<labwc>/environ is exec-time env only; kestrel-session starts labwc
  # without WAYLAND_DISPLAY (run 40466502343 proved: environ unset while the
  # socket exists), so the compositor cannot name its own socket this way.
  # The socket file itself is observed state: use it when exactly one
  # non-lock wayland socket exists in the runtime dir, else fail honestly.
  [ -n "$LX" ] || LX=/run/user/$(id -u)
  ls -l "$LX"/wayland-* 2>&1 | tee -a "$out"
  SOCKS=$(find "$LX" -maxdepth 1 -type s -name 'wayland-*' 2>/dev/null)
  if [ -z "$LW" ]; then
    case $(printf '%s\n' "$SOCKS" | grep -c .) in
      1) LW=$(basename "$SOCKS"); both "wayland display from observed single socket: $LW";;
      *) V='FAIL launch-env'; both "launch: FAILED (no unique wayland socket in $LX; refusing to guess)";;
    esac
  fi
  if [ -z "$LX" ] || [ -z "$LW" ] || [ ! -S "$LX/$LW" ]; then
    [ "$V" = PASS ] && V='FAIL launch-env'
    both "launch: FAILED (cannot establish display from observed state: XDG_RUNTIME_DIR=${LX:-unset} WAYLAND_DISPLAY=${LW:-unset})"
  else
    env XDG_RUNTIME_DIR="$LX" WAYLAND_DISPLAY="$LW" \
      flatpak run org.gnome.Calculator >>"$out" 2>&1 &
    sleep 25
    if pgrep -f gnome-calculator >/dev/null 2>&1; then
      both 'launch: calculator process alive 25s after flatpak run'
    else
      V='FAIL launch'; both 'launch: FAILED (no gnome-calculator process 25s after flatpak run)'
    fi
    # Rendered-window assertion through the compositor toplevel list (the
    # wlr-foreign-toplevel protocol the session taskbar already uses). A
    # live process alone does not prove a window; the app screenshot
    # remains the pixel gate on top of this.
    WINS=$(XDG_RUNTIME_DIR="$LX" kestrel-taskbar status 2>&1) && {
      both "taskbar toplevels: $WINS"
      if printf '%s' "$WINS" | grep -qi calculator; then
        both 'window: calculator toplevel present (compositor-registered)'
      else
        V='FAIL window'; both 'window: FAILED (no calculator toplevel in taskbar status)'
      fi
    } || both "window: taskbar status unavailable ($WINS); pixel gate only"
  fi
fi
# Verdict into the log for the host machine gate, then full-screen for the visual gate.
both "SMOKE_RESULT=$V"
# CI-only export. Single channel: a tiny HTTP server on guest :8766 (hostfwd
# 127.0.0.1:18766). The virtio CI console was dropped after failing its
# guest->host write in every run that exercised it ("ci-port: write failed",
# last seen run 40470957816) while :8766 carried the log every time.
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
LISTEN=$(ss -tln 2>/dev/null | grep -E ':(8765|8766) ' || true)
both "ci-listeners: ${LISTEN:-none}"
clear
echo "SMOKE_RESULT=$V"
echo "full log: $out"
echo "ci-listeners: ${LISTEN:-none}"
