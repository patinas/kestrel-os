#!/usr/bin/env bash
set -euo pipefail
exec >/dev/ttyS0 2>&1
systemctl start NetworkManager
for i in {1..30}; do getent hosts geo.mirror.pkgbuild.com && break; sleep 2; done
sleep 20
export KESTREL_ALLOW_VM_INSTALL=yes KESTREL_CONFIRM='ERASE /dev/vda'
export KESTREL_SRC_OVERLAY=/run/kestrelshare/profile/airootfs
export KESTREL_PACMAN_CONF=/run/kestrelshare/profile/pacman.conf
export KESTREL_UPDATE_PUB=/run/kestrelshare/out/test-keys/test.pub
bash /run/kestrelshare/scripts/install.sh /dev/vda
mkdir -p /run/testroot /run/testesp
for s in A B; do
 mount "/dev/disk/by-label/root$s" /run/testroot
 cp -a /run/kestrelshare/tests/overlay/. /run/testroot/
 umount /run/testroot
done
mount /dev/disk/by-label/KESTRELESP /run/testesp
sed -i '/^options /s/$/ console=tty0 console=ttyS0 kestrel.test-job kestrel.job=diagnostics/' /run/testesp/loader/entries/*.conf
mv /run/testesp/loader/entries/kestrel-A.conf /run/testesp/loader/entries/kestrel-A+3.conf
umount /run/testesp
sync
echo KESTREL_FULL_INSTALL_DONE
