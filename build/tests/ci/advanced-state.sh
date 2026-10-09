#!/usr/bin/env bash
# Regression: the Advanced state must show in /status and in the real Settings page, and an
# optional-feature failure (missing lock helper) must not break /status. Uses a copy of the real
# bridge and headless Chrome on loopback; no VM. Chrome is preinstalled on ubuntu-latest.
set -euo pipefail
R="$(cd "$(dirname "$0")/../../profile/airootfs" && pwd)"
T="$(mktemp -d)"; export HOME="$T"
sed "s|/usr/share/kestrel/shell/index.html|$R/usr/share/kestrel/shell/index.html|;s|/var/lib/kestrel/terminal-enabled|$T/enabled|g;s|/usr/local/bin/kestrel-lock-check|$T/missing-helper|" "$R/usr/local/bin/kestrel-shell-server" > "$T/s.py"
python3 "$T/s.py" >"$T/log" 2>&1 & SP=$!; trap 'kill $SP 2>/dev/null' EXIT
for i in $(seq 40); do curl -s -o /dev/null -H 'Host: 127.0.0.1:8765' http://127.0.0.1:8765/status && break; sleep 0.25; done
f(){ curl -s -H 'Host: 127.0.0.1:8765' http://127.0.0.1:8765/status | python3 -c "import sys,json;print(json.load(sys.stdin)['$1'])"; }
chk(){ [ "$1" = "$2" ] && echo "PASS $3" || { echo "FAIL $3 (got $1, want $2)"; tail -5 "$T/log"; exit 1; }; }
chk "$(f enabled)" False "status off without flag"
chk "$(f lock_enabled)" False "missing lock helper does not break /status"
page(){ google-chrome --headless=new --no-sandbox --disable-gpu --user-data-dir="$T/prof$1" --virtual-time-budget=6000 --dump-dom http://127.0.0.1:8765/ 2>/dev/null | grep -o 'id="state">[^<]*'; }
chk "$(page a)" 'id="state">Advanced access off' "page shows off"
touch "$T/enabled"
chk "$(f enabled)" True "status on after flag"
chk "$(page b)" 'id="state">Advanced access on' "page shows on (flag survives a fresh page load)"
rm "$T/enabled"
chk "$(page c)" 'id="state">Advanced access off' "page shows off after flag removed"
echo "advanced-state: all passed"
# Regression for a refresh that is already in flight when the flag flips: a second refresh()
# call must run after it, not reuse its stale answer (it used to be coalesced into it).
T2="$(mktemp -d)"; rm -f "$T/enabled"
python3 - "$T/s.py" "$T2/s2.py" "$T/enabled" <<'PY'
import sys
s=open(sys.argv[1]).read()
hook="""
import time as _t
_n=[0];_orig=status
def status():
 r=_orig()
 if _n[0]==0:
  _n[0]=1;_t.sleep(2);open('%s','w').write('')
 return r
"""%sys.argv[3]
s=s.replace("# Disposable CI guest only",hook+"# Disposable CI guest only",1)
s=s.replace("ORIGIN='http://127.0.0.1:8765'","ORIGIN='http://127.0.0.1:8765'",1)
open(sys.argv[2],'w').write(s)
PY
kill $SP 2>/dev/null; sleep 0.5
sed "s|</script>|refresh()</script>|" "$R/usr/share/kestrel/shell/index.html" > "$T2/index.html"
sed -i "s|$R/usr/share/kestrel/shell/index.html|$T2/index.html|" "$T2/s2.py"
python3 "$T2/s2.py" >"$T2/log" 2>&1 & SP=$!
for i in $(seq 40); do (echo > /dev/tcp/127.0.0.1/8765) 2>/dev/null && break; sleep 0.25; done
chk "$(google-chrome --headless=new --no-sandbox --disable-gpu --user-data-dir="$T/profd" --virtual-time-budget=9000 --dump-dom http://127.0.0.1:8765/ 2>/dev/null | grep -o 'id="state">[^<]*')" 'id="state">Advanced access on' "refresh requested during an in-flight stale refresh ends up current"
echo "advanced-state (in-flight): passed"
