#!/usr/bin/env bash
# Scoped guard for this disposable Kestrel VM test only. No production restarts.
set -u
cd "$(dirname "$0")/.."
while docker inspect -f '{{.State.Running}}' kestrel-m2-tests 2>/dev/null | grep -qx true; do
 started=$(date +%s)
 tmp=$(mktemp)
 code=$(curl -sS --max-time 25 -o "$tmp" -w '%{http_code}' http://127.0.0.1:3000/stream/672.m3u8 2>/dev/null || true)
 n=$(grep -c '^#EXTINF' "$tmp" 2>/dev/null || true)
 rm -f "$tmp"
 if [ "$code" != 200 ] || [ "${n:-0}" -lt 2 ]; then
  printf '%s TV_GUARD_FAILED code=%s segments=%s\n' "$(date -Is)" "$code" "$n" | tee out/m2-tests/TV_GUARD_FAILED
  docker exec kestrel-m2-tests python tests/qmp.py quit >/dev/null 2>&1 || true
  docker stop -t 5 kestrel-m2-tests >/dev/null 2>&1 || true
  exit 1
 fi
 printf '%s healthy code=%s segments=%s\n' "$(date -Is)" "$code" "$n"
 elapsed=$(( $(date +%s) - started ))
 [ "$elapsed" -ge 60 ] || sleep "$((60-elapsed))"
done
