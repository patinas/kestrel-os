#!/usr/bin/env bash
set -euo pipefail
sleep 150
cat /proc/cmdline
journalctl -b --no-pager -u kestrel-health.service -u systemd-bless-boot.service
export KESTREL_ALLOW_VM_UPDATE=yes
bash /run/kestrel-test/profile/airootfs/usr/local/lib/kestrel/update.sh /var/tmp/kestrel-update/root.tar.zst /var/tmp/kestrel-update/root.tar.zst.minisig
sed -i '/^options /s/$/ console=tty0 console=ttyS0 kestrel.test-job kestrel.job=diagnostics kestrel.test_crash_shell=1/' /boot/loader/entries/*+3.conf
sync
ls -l /boot/loader/entries
cat /boot/loader/entries/*+3.conf
echo KESTREL_ROLLBACK_TEST_ARMED
