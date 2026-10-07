#!/usr/bin/env bash
# Publish UI test evidence (JPEG frames, result JSON, short log excerpt) to the public orphan branch "ui-evidence".
# Uses only the workflow GITHUB_TOKEN (contents: write). Never force-pushes. Never publishes the tunnel URL, the full log or the ISO.
. "$(dirname "$0")/env.sh"
: "${GH_TOKEN:?GH_TOKEN missing}"
E=$VM/evidence-out; rm -rf "$E"; mkdir -p "$E"
cp "$VM"/ui-*.jpg "$E"/ 2>/dev/null || true
for j in ui-state-results.json control-results.json; do [ ! -f "$VM/$j" ] || cp "$VM/$j" "$E/$j"; done
{ [ ! -f "$VM/ui-log.txt" ] || grep -E '^(ADVANCED_OWNERSHIP|PROBE_DIAGNOSTIC|DIALOG_OPEN|DIALOG_CLICK|PWA_|CDP_RECONNECT|SETTINGS_DIALOG|SETTINGS_CARD|RESULTS_WRITE|QUICK_|BRING_TO_FRONT|TITLEBAR_|TASKBAR_|CONTROL_RESULT|CONTROL_FINAL|UI_STATE|AUDIO_EFFECT|SETTINGS_TARGETS_AFTER_MOUSE|Traceback|  File |[A-Za-z]+Error|StopIteration|RuntimeError)' "$VM/ui-log.txt"; } > "$E/log-excerpt.txt" || true
# Privacy gate: only these file types, and refuse anything that looks like a URL, email or token.
find "$E" -type f ! \( -name '*.jpg' -o -name '*.json' -o -name 'log-excerpt.txt' \) -delete
if grep -Eil 'trycloudflare|@[a-z0-9-]+\.[a-z]|ghp_|github_pat_|gho_|ghs_|password=|token=' "$E"/*.json "$E"/log-excerpt.txt 2>/dev/null; then echo 'privacy gate: suspicious text in evidence, not publishing'; exit 1; fi
n=$(ls "$E"/*.jpg 2>/dev/null | wc -l); echo "evidence frames: $n"; [ "$n" -gt 0 ] || { echo 'no frames to publish'; exit 1; }
run="run-${GITHUB_RUN_ID}-${GITHUB_SHA:0:7}"
{ echo "# Kestrel UI evidence $run"; echo; echo "Source: $GITHUB_SHA"; echo "Frames are 1280x800 screendumps of a disposable test VM (no accounts, no personal data), JPEG quality 48."; echo; for f in "$E"/*.jpg; do echo "- $(basename "$f")"; done; } > "$E/INDEX.md"
{
 echo '## UI_STATE_RESULTS'
 if [ -f "$E/ui-state-results.json" ]; then
  python3 - "$E/ui-state-results.json" <<'PY'
import json,sys
r=json.load(open(sys.argv[1]));c={}
for x in r:c[x['result']]=c.get(x['result'],0)+1
print('Totals: '+', '.join(f'{k} {v}' for k,v in sorted(c.items()))+'\n')
print('| Result | Check | Detail |\n|---|---|---|')
for x in r:print('| %s | %s | %s |'%(x['result'],x['check'].replace('|','/'),str(x['detail']).replace('|','/')[:140]))
PY
 else echo 'ui-state-results.json missing (script did not finish)'; fi
 echo; echo "Frames: https://github.com/$GITHUB_REPOSITORY/tree/ui-evidence/$run"
} >> "$GITHUB_STEP_SUMMARY"
URL=${EVIDENCE_REMOTE_URL:-"https://github.com/$GITHUB_REPOSITORY.git"}
auth=$(printf 'x-access-token:%s' "$GH_TOKEN" | base64 -w0); echo "::add-mask::$auth"
g(){ git -c "http.https://github.com/.extraheader=AUTHORIZATION: basic $auth" "$@"; }
for attempt in 1 2 3; do
 W=$(mktemp -d); cd "$W"; git init -q
 git config user.name 'kestrel-ci'; git config user.email 'ci@users.noreply.github.com'
 if g ls-remote --exit-code --heads "$URL" ui-evidence >/dev/null 2>&1; then g fetch -q "$URL" ui-evidence && git checkout -q -B ui-evidence FETCH_HEAD
 else git checkout -q --orphan ui-evidence; fi
 mkdir -p "$run"; cp "$E"/* "$run"/
 git add -A "$run"; git commit -q -m "UI evidence $run"
 if g push -q "$URL" ui-evidence; then echo "published: https://github.com/$GITHUB_REPOSITORY/tree/ui-evidence/$run"; exit 0; fi
 echo "push attempt $attempt failed (race or permission), retrying"; sleep 5
done
echo 'publish failed after 3 attempts'; exit 1
