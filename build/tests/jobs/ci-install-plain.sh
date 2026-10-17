#!/usr/bin/env bash
# CI: runs in the live ISO guest (systemd.run). Installs with the current repo overlay from the read-only 9p share,
# exactly as a real user install: no test overlay, no test kernel arguments, entries stay as the installer wrote them.
set -Eeuo pipefail
say(){ printf '%s\n' "$*" > /dev/ttyS0; }
trap 'say "CI_FAIL install line $LINENO"' ERR
exec >/dev/ttyS0 2>&1
S=/run/kestrelshare
systemctl start NetworkManager
for i in {1..60}; do getent hosts geo.mirror.pkgbuild.com && break; sleep 2; done
getent hosts geo.mirror.pkgbuild.com
sleep 20
export KESTREL_CONFIRM='ERASE /dev/vda'
export KESTREL_SRC_OVERLAY=$S/profile/airootfs KESTREL_PACMAN_CONF=$S/profile/pacman.conf
export KESTREL_GAME_LAUNCHERS=$(cat "$S/ci-launchers")
export KESTREL_UPDATE_PUB=$S/out/test-keys/test.pub
bash $S/scripts/install.sh /dev/vda
# CI-only direct Chrome setup in persistent home, authorized owner terms acceptance (WhatsApp 4 Oct 12:40:56).
mkdir -p /run/testdata; mount /dev/disk/by-label/kdata /run/testdata
runuser -u kestrel -- env HOME=/run/testdata/home/kestrel bash -c 'printf "ACCEPT\n" | /usr/local/bin/kestrel-chrome-setup'
test -x /run/testdata/home/kestrel/.local/share/kestrel/chrome/current/opt/google/chrome/chrome
umount /run/testdata
say "CI_STEP chrome_direct_download_signature_verified"
say "CI_INSTALL_DONE"
systemctl poweroff
