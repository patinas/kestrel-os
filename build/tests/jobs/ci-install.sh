#!/usr/bin/env bash
# CI: runs in the live ISO guest (systemd.run). Installs with the current repo overlay from the read-only 9p share.
set -Eeuo pipefail
say(){ printf '%s\n' "$*" > /dev/ttyS0; }
trap 'say "CI_FAIL install line $LINENO"' ERR
exec >/dev/ttyS0 2>&1
S=/run/kestrelshare
systemctl start NetworkManager
for i in {1..60}; do getent hosts geo.mirror.pkgbuild.com && break; sleep 2; done
getent hosts geo.mirror.pkgbuild.com
sleep 20
export KESTREL_ALLOW_VM_INSTALL=yes KESTREL_CONFIRM='ERASE /dev/vda'
export KESTREL_SRC_OVERLAY=$S/profile/airootfs KESTREL_PACMAN_CONF=$S/profile/pacman.conf
export KESTREL_UPDATE_PUB=$S/out/test-keys/test.pub
bash $S/scripts/install.sh /dev/vda
mkdir -p /run/testroot /run/testesp
for s in A B; do
  mount "/dev/disk/by-label/root$s" /run/testroot
  # test overlay (job service, run-job.sh, health drop-in); cp -a keeps its symlink
  cp -a $S/tests/overlay/. /run/testroot/
  chmod 755 /run/testroot/usr/local/lib/kestrel-test/run-job.sh
  # No interactive serial login in CI. Getty resets can invalidate a job's open tty fd.
  ln -sfn /dev/null /run/testroot/etc/systemd/system/serial-getty@ttyS0.service
  umount /run/testroot
done
mount /dev/disk/by-label/KESTRELESP /run/testesp
sed -i '/^options /s/$/ console=tty0 console=ttyS0 kestrel.test-job kestrel.job=ci/' /run/testesp/loader/entries/kestrel-A.conf /run/testesp/loader/entries/kestrel-B.conf
# Arm A with 3 tries so the first boot proves health + bless; B stays a counter-less entry.
mv /run/testesp/loader/entries/kestrel-A.conf /run/testesp/loader/entries/kestrel-A+3.conf
ls -l /run/testesp/loader/entries; cat /run/testesp/loader/loader.conf
umount /run/testesp
sync
say "CI_INSTALL_DONE"
systemctl poweroff
