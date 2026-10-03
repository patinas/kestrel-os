#!/usr/bin/env bash
# CI state machine, run at each boot of the installed guest by kestrel-test-job.service (kernel arg kestrel.job=ci).
# Stage lives on the writable data partition. Evidence goes to the serial console as CI_* lines.
set -Eeuo pipefail
say(){ printf '%s\n' "$*" > /dev/ttyS0; }
trap 'say "CI_FAIL line $LINENO (slot=${slot:-?} stage=${stage:-?})"; journalctl -b --no-pager -u kestrel-health.service -u systemd-bless-boot.service | tail -n 40 > /dev/ttyS0; ls -l /boot/loader/entries > /dev/ttyS0 2>&1' ERR
exec >/dev/ttyS0 2>&1
T=/run/kestrel-test; KEY=$T/out/test-keys/test.key; WAIT=$(cat $T/ci-wait)
ST=/var/lib/kestrel-ci; mkdir -p $ST
stage=$(cat $ST/stage 2>/dev/null || echo 0)
slot=$(sed -n 's/.*kestrel\.slot=\([AB]\).*/\1/p' /proc/cmdline)
ENT=/boot/loader/entries
ls /boot >/dev/null            # trigger ESP automount
fail(){ say "CI_FAIL $*"; exit 1; }
health_ok(){ journalctl -b --no-pager -u kestrel-health.service | grep -q 'kestrel-health: OK'; }
health_failed(){ journalctl -b --no-pager -u kestrel-health.service | grep -q 'kestrel-health: FAIL'; }
wait_for(){ # wait_for <seconds> <cmd...>
  local t=$1; shift; local i=0; until "$@"; do sleep 5; i=$((i+5)); [ $i -lt "$t" ] || return 1; done; }
blessed(){ [ -f "$ENT/kestrel-$slot.conf" ] && ! ls "$ENT"/kestrel-"$slot"+*.conf >/dev/null 2>&1; }
wait_blessed(){
  wait_for "$WAIT" blessed || fail "slot $slot not blessed within ${WAIT}s"
  health_ok || fail "blessed but no health OK in journal"
  findmnt -no OPTIONS / | tr ',' '\n' | grep -qx ro || fail "root not read-only"
  say "CI_EVIDENCE entries:"; ls -l "$ENT" > /dev/ttyS0
  journalctl -b --no-pager -u kestrel-health.service -u systemd-bless-boot.service | tail -n 12 > /dev/ttyS0
}
append_opts(){ sed -i '/^options /s/$/ console=tty0 console=ttyS0 kestrel.test-job kestrel.job=ci '"$2"'/' "$1"; }
do_update(){ # do_update <extra options for the new entry>
  local d=/var/tmp/kestrel-update; rm -rf $d; mkdir -p $d
  /usr/local/lib/kestrel/make-test-update.sh "$KEY" $d > $d/make.log 2>&1 || { tail -n 30 $d/make.log; fail "make-test-update failed"; }
  export KESTREL_ALLOW_VM_UPDATE=yes
  kestrel-update $d/root.tar.zst $d/root.tar.zst.minisig || fail "signed update failed"
  local e; e=$(ls "$ENT"/kestrel-*+3.conf); [ "$(echo "$e" | wc -l)" = 1 ] || fail "expected exactly one armed entry"
  append_opts "$e" "$1"
  say "CI_EVIDENCE armed entry $e:"; cat "$e" > /dev/ttyS0
  rm -rf $d
}
poweroff_now(){ echo "$1" > $ST/stage; sync; say "CI_POWEROFF stage=$1"; systemctl poweroff; sleep 600; }
say "CI_BOOT slot=$slot stage=$stage cmdline=$(cat /proc/cmdline)"
case "$stage" in
0) [ "$slot" = A ] || fail "stage 0 expected slot A"
   ls "$ENT"/kestrel-A+*.conf >/dev/null 2>&1 || ls "$ENT"/kestrel-A.conf >/dev/null || fail "no A entry"
   wait_blessed; say "CI_STEP boot_A_health_and_bless_ok"
   # bad detached signature must be rejected by the real verifier before any slot/entry write
   d=/var/tmp/kestrel-update; mkdir -p $d
   /usr/local/lib/kestrel/make-test-update.sh "$KEY" $d > $d/make.log 2>&1 || fail "make-test-update failed"
   python3 - <<PY
p="$d/root.tar.zst.minisig"; l=open(p).read().split("\n")
s=l[1]; i=10; l[1]=s[:i]+("B" if s[i]=="A" else "A")+s[i+1:]; open(p,"w").write("\n".join(l))
PY
   before=$(sha256sum $ENT/*.conf | sha256sum); uuid=$(blkid -s UUID -o value /dev/disk/by-label/rootB)
   export KESTREL_ALLOW_VM_UPDATE=yes
   say "CI_DIAGNOSTIC signature files and updater"
   ls -l "$d" /usr/local/bin/kestrel-update /usr/local/lib/kestrel/update.sh > /dev/ttyS0 2>&1 || fail "signature files/updater listing failed"
   rc=0
   kestrel-update "$d/root.tar.zst" "$d/root.tar.zst.minisig" > "$d/bad.log" 2>&1 || rc=$?
   say "CI_DIAGNOSTIC bad-signature exit=$rc log=$d/bad.log"
   [ "$rc" -ne 0 ] || fail "bad signature accepted"
   if [ -r "$d/bad.log" ]; then cat "$d/bad.log" > /dev/ttyS0; else fail "bad-signature log missing"; fi
   if ! grep -q "signature verification FAILED" "$d/bad.log"; then fail "rejection message missing (exit=$rc)"; fi
   [ "$before" = "$(sha256sum $ENT/*.conf | sha256sum)" ] || fail "entries changed after bad signature"
   [ "$uuid" = "$(blkid -s UUID -o value /dev/disk/by-label/rootB)" ] || fail "rootB rewritten after bad signature"
   say "CI_STEP bad_signature_rejected_no_writes"
   rm -rf $d
   do_update ""
   [ -f $ENT/kestrel-A.conf ] && ls $ENT/kestrel-B+3.conf >/dev/null || fail "A known-good/B armed entries wrong"
   say "CI_STEP signed_update_A_to_B_armed_fallback_preserved"
   poweroff_now 1 ;;
1) [ "$slot" = B ] || fail "stage 1 expected slot B, booted $slot (fallback or default wrong)"
   wait_blessed; say "CI_STEP boot_B_after_update_health_and_bless_ok"
   do_update ""
   [ -f $ENT/kestrel-B.conf ] && ls $ENT/kestrel-A+3.conf >/dev/null || fail "B known-good/A armed entries wrong"
   say "CI_STEP signed_update_B_to_A_armed"
   poweroff_now 2 ;;
2) [ "$slot" = A ] || fail "stage 2 expected slot A, booted $slot"
   wait_blessed; say "CI_STEP boot_A_after_B_to_A_update_ok"
   do_update "kestrel.test_crash_shell=1"
   echo 0 > $ST/tries
   say "CI_STEP unhealthy_update_armed"
   echo 3 > $ST/stage; sync; say "CI_REBOOT stage=3"; systemctl reboot; sleep 600 ;;
3) tries=$(cat $ST/tries 2>/dev/null || echo 0)
   if [ "$slot" = B ]; then
     tries=$((tries+1)); echo $tries > $ST/tries
     [ $tries -le 3 ] || fail "unhealthy slot B booted $tries times (more than 3 tries)"
     grep -qw kestrel.test_crash_shell=1 /proc/cmdline || fail "crash flag missing on slot B"
     wait_for "$WAIT" health_failed || fail "unhealthy boot did not fail the health gate"
     [ ! -f $ENT/kestrel-B.conf ] || fail "unhealthy boot was blessed"
     ! health_ok || fail "health unexpectedly OK"
     say "CI_STEP unhealthy_boot_${tries}_gate_failed_unblessed"; ls -l $ENT > /dev/ttyS0
     say "CI_REBOOT after failed try $tries"; systemctl reboot; sleep 600
   else
     [ "$tries" = 3 ] || fail "fell back to A after only $tries failed tries"
     ls $ENT/kestrel-B+0-*.conf >/dev/null 2>&1 || { ls -l $ENT; fail "B entry not exhausted (+0)"; }
     grep -qw kestrel.test_crash_shell=1 /proc/cmdline && fail "fallback boot carries crash flag"
     wait_for "$WAIT" health_ok || fail "fallback A not healthy"
     [ -f $ENT/kestrel-A.conf ] || fail "A known-good entry missing"
     say "CI_STEP fallback_to_known_good_A_after_3_failed_tries"; ls -l $ENT > /dev/ttyS0
     say "CI_DONE_OK"; echo 4 > $ST/stage; sync; say "CI_POWEROFF stage=4"; systemctl poweroff; sleep 600
   fi ;;
*) fail "unknown stage $stage" ;;
esac
