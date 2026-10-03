#!/usr/bin/env bash
set -euo pipefail
exec >/dev/ttyS0 2>&1
case "$(systemd-detect-virt --vm)" in qemu|kvm) ;; *) exit 1;; esac
[ "$(cat /sys/block/vda/serial)" = KESTREL_TEST_ONLY ]
mkdir -p /run/rescue /run/esp
mount /dev/disk/by-label/rootB /run/rescue
install -d -m 755 /run/rescue/run
install -d -m 1777 /run/rescue/tmp
chmod 755 /run/rescue/usr/local/bin/kestrel-*
cp /run/kestrelshare/profile/airootfs/usr/local/lib/kestrel/update.sh /run/rescue/usr/local/lib/kestrel/update.sh
ls -ld /run/rescue/{run,tmp,dev,proc,sys,var,home,etc}
umount /run/rescue
mount /dev/disk/by-label/KESTRELESP /run/esp
ls -l /run/esp/loader/entries
umount /run/esp
sync
echo KESTREL_RESCUE_REPAIR_DONE
