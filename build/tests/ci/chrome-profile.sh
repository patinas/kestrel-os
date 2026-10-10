#!/usr/bin/env bash
# Regression: the real kestrel-browser start-up seeds a Chrome profile with vertical tabs on and the
# system title bar (one close button, not two), and real Chrome renders a vertical tab strip.
# Runs real Chrome under Xvfb on loopback. No VM. Needs google-chrome, Xvfb and ImageMagick.
set -euo pipefail
R="$(cd "$(dirname "$0")/../../profile/airootfs" && pwd)"
command -v Xvfb >/dev/null && command -v import >/dev/null || { sudo apt-get update -qq && sudo apt-get install -y -qq xvfb imagemagick x11-utils >/dev/null; }
CHROME="$(dirname "$(readlink -f "$(command -v google-chrome)")")"
T="$(mktemp -d)"; export HOME="$T"
mkdir -p "$T/.local/share/kestrel/chrome/current/opt/google" && ln -s "$CHROME" "$T/.local/share/kestrel/chrome/current/opt/google/chrome"
# Test copy: X11 under Xvfb instead of Wayland, and the CI sandbox flag. Everything else is the shipped script.
sed 's|--ozone-platform=wayland|--ozone-platform=x11 --no-sandbox --window-size=1200,760 --window-position=0,0|;s|--start-maximized||' "$R/usr/local/bin/kestrel-browser" > "$T/kb"
chk(){ [ "$1" = "$2" ] && echo "PASS $3" || { echo "FAIL $3 (got $1, want $2)"; exit 1; }; }
pref(){ python3 -c "import json;p=json.load(open('$T/.config/kestrel-chrome/Default/Preferences'));print($1)"; }
Xvfb :88 -screen 0 1280x800x24 >/dev/null 2>&1 & XP=$!; trap 'kill $XP $CP 2>/dev/null || true' EXIT; sleep 1
DISPLAY=:88 bash "$T/kb" 'data:text/html,<title>Kestrel</title>x' >"$T/chrome.log" 2>&1 & CP=$!
# Slow runners: wait (up to 60s) for the Preferences file and a mapped Chrome window, then let it paint.
for _ in $(seq 60); do [ -s "$T/.config/kestrel-chrome/Default/Preferences" ] && DISPLAY=:88 xwininfo -root -tree 2>/dev/null | grep -q "Kestrel" && break; sleep 1; done
sleep 8
echo "chrome: $(google-chrome --version)"; DISPLAY=:88 xwininfo -root -tree 2>/dev/null | grep -E '"[^"]+"' | head -8 || true
chk "$(pref "p['vertical_tabs']['enabled']")" True "vertical_tabs.enabled persisted by real Chrome"
chk "$(pref "p['browser']['custom_chrome_frame']")" False "system title bar (single close button)"
shotpix(){ DISPLAY=:88 import -window root "$T/shot.png"; cp "$T/shot.png" "${KESTREL_SHOT_OUT:-/tmp/chrome-profile-shot.png}"; convert "$T/shot.png" -depth 8 "$T/shot.ppm"; }
shotpix
pixcheck(){ python3 - "$T/shot.ppm" <<'PY'
import sys
d=open(sys.argv[1],'rb').read();parts=d.split(b'\n',3);w,h=map(int,parts[1].split());px=parts[3]
def at(x,y):i=(y*w+x)*3;return tuple(px[i:i+3])
side,content=at(100,400),at(700,400)
# Vertical strip: a tinted side panel at the left, white page content to the right. A horizontal strip leaves (100,400) white.
ok=side!=(255,255,255) and content==(255,255,255) and abs(side[2]-side[0])>15
print(("PASS" if ok else "FAIL"),"vertical tab strip rendered on the left",side,content);sys.exit(0 if ok else 1)
PY
}
pixcheck || { sleep 10; shotpix; pixcheck; }
# Second start must keep the user's choice: switching vertical tabs off is not undone.
kill $CP; sleep 3
python3 - "$T" <<'PY'
import json,sys;f=sys.argv[1]+'/.config/kestrel-chrome/Default/Preferences';p=json.load(open(f));p['vertical_tabs']['enabled']=False;p['browser']['custom_chrome_frame']=True;json.dump(p,open(f,'w'))
PY
pkill -u "$(id -u)" -x chrome 2>/dev/null || true; sleep 2
DISPLAY=:88 bash "$T/kb" about:blank >>"$T/chrome.log" 2>&1 & CP=$!; sleep 8; kill $CP; sleep 2; pkill -u "$(id -u)" -x chrome 2>/dev/null || true; sleep 1
chk "$(pref "p['vertical_tabs']['enabled']")" False "user's vertical-tabs choice kept on later starts"
chk "$(pref "p['browser']['custom_chrome_frame']")" False "double-close-button setting re-enforced on every start"
echo "chrome-profile: all passed"
