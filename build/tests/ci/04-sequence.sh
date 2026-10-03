#!/usr/bin/env bash
# Drive disk-only boots. The guest state machine (jobs/ci.sh) does the real work; this loop relaunches QEMU after
# each guest poweroff (persistent OVMF vars file across process restarts) until CI_DONE_OK or a failure.
. "$(dirname "$0")/env.sh"; . "$(dirname "$0")/qemu.sh"
tmo=5400; [ "$ACCEL" = kvm ] || tmo=21600
n=0
while [ $n -lt 8 ]; do
  n=$((n+1)); log="$VM/serial-run$n.log"; say "launch $n ($ACCEL)"
  rc=0; qemu_launch "$log" "$tmo" -boot c || rc=$?
  grep -E '^CI_(STEP|POWEROFF|DONE_OK|FAIL)' "$log" || true
  if grep -q '^CI_DONE_OK' "$log"; then echo "sequence complete"; exit 0; fi
  if [ "$rc" -ne 0 ]; then echo "::error::launch $n failed (rc=$rc)"; tail -n 150 "$log"; exit 1; fi
  grep -q '^CI_POWEROFF' "$log" || { echo "::error::guest exited without a stage poweroff"; tail -n 150 "$log"; exit 1; }
done
echo "::error::too many launches without completion"; exit 1
