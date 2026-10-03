#!/usr/bin/env bash
set -euo pipefail
sleep 150
systemctl is-active kestrel-health.service || true
journalctl -b --no-pager -u kestrel-health.service -u systemd-bless-boot.service
cat /proc/cmdline
mkdir -p /var/tmp/kestrel-update
bash /usr/local/lib/kestrel/make-test-update.sh /run/kestrel-test/out/test-keys/test.key /var/tmp/kestrel-update
export KESTREL_ALLOW_VM_UPDATE=yes
# A corrupted detached signature must be rejected before slot or entry writes.
cp /var/tmp/kestrel-update/root.tar.zst.minisig /var/tmp/kestrel-update/bad.minisig
sed -i '2s/./A/10' /var/tmp/kestrel-update/bad.minisig
before=$(sha256sum /boot/loader/entries/*.conf)
if kestrel-update /var/tmp/kestrel-update/root.tar.zst /var/tmp/kestrel-update/bad.minisig > /var/tmp/bad-signature.log 2>&1; then echo BAD_SIGNATURE_ACCEPTED; exit 1; fi
cat /var/tmp/bad-signature.log
grep -q "signature verification FAILED" /var/tmp/bad-signature.log
[ "$before" = "$(sha256sum /boot/loader/entries/*.conf)" ]
echo BAD_SIGNATURE_REJECTED_ENTRIES_UNCHANGED
kestrel-update /var/tmp/kestrel-update/root.tar.zst /var/tmp/kestrel-update/root.tar.zst.minisig
sed -i '/^options /s/$/ console=tty0 console=ttyS0 kestrel.test-job kestrel.job=diagnostics/' /boot/loader/entries/*+3.conf
sync
ls -l /boot/loader/entries
cat /boot/loader/entries/*+3.conf
echo KESTREL_SIGNED_UPDATE_ARMED
