#!/usr/bin/env bash
# Kestrel boot health gate. Runs from kestrel-health.service, ordered before boot-complete.target.
# systemd-bless-boot only marks the entry good if this exits 0. Never tests external internet.
set -u
SESSION_USER=kestrel
HOLD=${KESTREL_HEALTH_HOLD:-60}     # seconds the same processes must survive
WAITMAX=${KESTREL_HEALTH_WAIT:-120} # seconds to wait for the session to appear
log(){ echo "kestrel-health: $*"; }
fail(){ log "FAIL: $*"; exit 1; }
# pid + start time identity, so a restarted process with a reused name does not pass
ident(){ local p=$1; [ -r /proc/$p/stat ] || return 1; echo "$p:$(awk '{print $22}' /proc/$p/stat | head -1)"; }
find_pid(){ pgrep -u "$SESSION_USER" -x -o "$1" 2>/dev/null; }
comp= cli=
t=0
while [ $t -lt $WAITMAX ]; do
  for c in cage gamescope; do p=$(find_pid $c) && [ -n "$p" ] && { comp=$p; compn=$c; break; }; done
  if [ -n "$comp" ]; then
    case $compn in cage) names="chromium";; gamescope) names="steam";; esac
    for n in $names; do p=$(find_pid $n) && [ -n "$p" ] && { cli=$p; clin=$n; break; }; done
  fi
  [ -n "$comp" ] && [ -n "$cli" ] && break
  comp= cli=; sleep 2; t=$((t+2))
done
[ -n "$comp" ] && [ -n "$cli" ] || fail "compositor/browser not running after ${WAITMAX}s"
id1=$(ident "$comp") || fail "compositor vanished"; id2=$(ident "$cli") || fail "$clin vanished"
log "tracking $compn=$id1 $clin=$id2 for ${HOLD}s"
# Static checks (offline-safe)
opts=$(findmnt -no OPTIONS / ) ; case ",$opts," in *,ro,*) ;; *) fail "root is not read-only ($opts)";; esac
[ -r /usr/share/kestrel/shell/index.html ] || fail "local shell page missing"
# Test-only fault injection, only when the kernel cmdline asks for it (used to prove unhealthy boots stay unblessed)
if grep -qw kestrel.test_crash_shell=1 /proc/cmdline; then sleep 15; pkill -u "$SESSION_USER" -x "$clin" || true; fi
i=0
while [ $i -lt "$HOLD" ]; do
  sleep 2; i=$((i+2))
  [ "$(ident "$comp" 2>/dev/null)" = "$id1" ] || fail "$compn restarted or died"
  [ "$(ident "$cli" 2>/dev/null)" = "$id2" ] || fail "$clin restarted or died"
done
log "OK"
exit 0
