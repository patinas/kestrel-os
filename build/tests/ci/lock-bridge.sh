#!/usr/bin/env bash
# Exercise /lock-set, /lock-clear and /status through a copy of the real bridge on loopback. No VM.
set -euo pipefail
R="$(cd "$(dirname "$0")/../../profile/airootfs" && pwd)"
T="$(mktemp -d)"; export HOME="$T" KESTREL_LOCK_FILE="$T/lock.json" PATH="$R/usr/local/bin:$PATH"
sed "s|/usr/share/kestrel/shell/index.html|$R/usr/share/kestrel/shell/index.html|" "$R/usr/local/bin/kestrel-shell-server" > "$T/server.py"
python3 "$T/server.py" & SP=$!; trap 'kill $SP 2>/dev/null' EXIT
for i in $(seq 40); do curl -s -o /dev/null -H 'Host: 127.0.0.1:8765' http://127.0.0.1:8765/status && break; sleep 0.25; done
TOK=$(curl -s -H 'Host: 127.0.0.1:8765' http://127.0.0.1:8765/ | grep -o "'X-Kestrel-Token':'[^']*'" | head -1 | cut -d"'" -f4)
[ -n "$TOK" ] && [ "$TOK" != BRIDGE_TOKEN ] || { echo "FAIL token not injected"; exit 1; }
post(){ curl -s -o /dev/null -w '%{http_code}' -X POST -H 'Host: 127.0.0.1:8765' -H 'Origin: http://127.0.0.1:8765' -H "X-Kestrel-Token: $TOK" -H 'Content-Type: application/json' -d "$2" "http://127.0.0.1:8765$1"; }
st(){ curl -s -H 'Host: 127.0.0.1:8765' http://127.0.0.1:8765/status | python3 -c 'import sys,json;print(json.load(sys.stdin)["lock_enabled"])'; }
chk(){ [ "$1" = "$2" ] && echo "PASS $3" || { echo "FAIL $3 (got $1, want $2)"; exit 1; }; }
chk "$(st)" False "status off"
chk "$(post /lock-set '{"password":"short"}')" 400 "short rejected"
chk "$(post /lock-set '{"password":"long enough pw"}')" 204 "set"
chk "$(st)" True "status on"
chk "$(post /lock-set '{"password":"another long pw","current":"nope"}')" 403 "change wrong current"
chk "$(post /lock-clear '{"current":"nope"}')" 403 "clear wrong current"
chk "$(curl -s -o /dev/null -w '%{http_code}' -X POST -H 'Host: 127.0.0.1:8765' -H 'Origin: http://evil.example' -H "X-Kestrel-Token: $TOK" -d '{}' http://127.0.0.1:8765/lock-clear)" 403 "bad origin"
chk "$(post /lock-clear '{"current":"long enough pw"}')" 204 "clear"
chk "$(st)" False "status off again"
echo "lock-bridge: all passed"
