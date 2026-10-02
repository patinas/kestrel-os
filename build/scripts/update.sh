#!/usr/bin/env bash
# Kestrel A/B updater, VM-ONLY. Usage: update.sh root.tar.zst root.tar.zst.minisig
# Verifies the signature, determines the ACTIVE slot from the kernel cmdline, checks the inactive slot's
# device is on the same disk as the ESP, writes it, and arms a 3-try boot of the new slot.
set -Eeuo pipefail
. "$(dirname "$0")/lib.sh"
need_root
IMG=${1:?root.tar.zst}; SIG=${2:?signature .minisig}
PUB=${KESTREL_UPDATE_PUB:-/etc/kestrel/update.pub}
[ "${KESTREL_ALLOW_VM_UPDATE:-}" = yes ] || die "set KESTREL_ALLOW_VM_UPDATE=yes (VM-only)"
command -v minisign >/dev/null || die "minisign not installed"
[ -f "$PUB" ] || die "no public key at $PUB"
minisign -Vm "$IMG" -p "$PUB" -x "$SIG" >/dev/null || die "signature verification FAILED; refusing"
# Active slot from cmdline (root=LABEL=rootA|rootB), must also match the mounted root's label
ACT=$(sed -n 's/.*root=LABEL=root\([AB]\).*/\1/p' /proc/cmdline)
[ -n "$ACT" ] || die "cannot determine active slot"
MNTLABEL=$(findmnt -no LABEL / || true)
[ "$MNTLABEL" = "root$ACT" ] || die "mounted root label ($MNTLABEL) disagrees with cmdline slot ($ACT)"
case $ACT in A) NEW=B;; B) NEW=A;; esac
ACTDEV=$(blkid -L "root$ACT"); NEWDEV=$(blkid -L "root$NEW"); ESPDEV=$(blkid -L KESTRELESP)
[ -b "$NEWDEV" ] && [ -b "$ESPDEV" ] || die "slot/ESP device missing"
[ "$NEWDEV" != "$ACTDEV" ] || die "target equals active slot"
D1=$(lsblk -no PKNAME "$NEWDEV"); D2=$(lsblk -no PKNAME "$ESPDEV"); D3=$(lsblk -no PKNAME "$ACTDEV")
[ "$D1" = "$D2" ] && [ "$D1" = "$D3" ] || die "slots and ESP are not on the same disk"
is_vm_disk "/dev/$D1" || die "/dev/$D1 is not a VM/loop disk; refusing"
findmnt -n "$NEWDEV" >/dev/null && die "inactive slot is mounted; refusing"
W=$(mktemp -d)
cleanup(){ set +e; umount "$W/new" 2>/dev/null; umount "$W/esp" 2>/dev/null; rm -rf "$W"; }
trap cleanup EXIT
mkdir -p "$W/new" "$W/esp"
mkfs.ext4 -qF -L "root$NEW" "$NEWDEV"        # device verified above, not label-resolved at write time
mount "$NEWDEV" "$W/new"
tar --zstd -xpf "$IMG" -C "$W/new" --numeric-owner
[ -f "$W/new/boot/vmlinuz-linux" ] && [ -f "$W/new/boot/initramfs-linux.img" ] || die "image lacks kernel/initramfs"
mount "$ESPDEV" "$W/esp"; mkdir -p "$W/esp/$NEW"
cp "$W/new/boot/vmlinuz-linux" "$W/new/boot/initramfs-linux.img" "$W/esp/$NEW/"
# 3 boot tries: systemd-boot renames the entry kestrel-X+3 -> counts down; bless-boot marks good
cat > "$W/esp/loader/entries/kestrel-$NEW+3.conf" <<L
title Kestrel OS ($NEW)
linux /$NEW/vmlinuz-linux
initrd /$NEW/initramfs-linux.img
options root=LABEL=root$NEW ro quiet kestrel.slot=$NEW
L
rm -f "$W/esp/loader/entries/kestrel-$NEW.conf"
sync
bootctl set-default "kestrel-$NEW+3.conf" 2>/dev/null || bootctl set-oneshot "kestrel-$NEW+3.conf"
echo "Experimental: slot $NEW written. Health/bless-boot integration is missing; automatic rollback is NOT verified."
