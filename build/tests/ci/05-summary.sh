#!/usr/bin/env bash
# Evidence for the job log and step summary. Logs are not uploaded anywhere.
[ -n "${CI_DIR:-}" ] || exit 0
. "$(dirname "$0")/env.sh"
{
  echo "## Kestrel VM test (accel: ${ACCEL})"
  echo '```'
  cat "$VM"/serial-install.log "$VM"/serial-run*.log 2>/dev/null | grep -E '^(CI_|root slot usage|Installed to)' || echo "no markers recorded"
  echo '```'
} | tee -a "${GITHUB_STEP_SUMMARY:-/dev/null}"
for f in "$VM"/serial-run*.log; do [ -f "$f" ] && { echo "::group::tail $(basename "$f")"; tail -n 80 "$f"; echo "::endgroup::"; }; done
df -h "$CI_DIR" || true
