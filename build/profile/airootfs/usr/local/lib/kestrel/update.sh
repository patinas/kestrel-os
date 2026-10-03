#!/usr/bin/env bash
# Kestrel A/B updater, VM-ONLY. Usage: update.sh root.tar.zst root.tar.zst.minisig
# Verifies the signature, determines the ACTIVE slot from the kernel cmdline, checks the inactive slot's
# device is on the same disk as the ESP, writes it, and arms a 3-try boot of the new slot (boot assessment).
set -Eeuo pipefail
. "$(dirname "$(readlink -f "$0")")/lib.sh"
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
# The running slot must itself be known good (counter-less entry exists), otherwise fallback would be unproven
[ -f /boot/loader/entries/kestrel-$ACT.conf ] || { systemctl start boot.automount 2>/dev/null || true; ls /boot >/dev/null 2>&1; }
[ -f /boot/loader/entries/kestrel-$ACT.conf ] || die "no known-good entry kestrel-$ACT.conf (current boot not blessed?); refusing"
ACTDEV=$(blkid -L "root$ACT"); NEWDEV=$(blkid -L "root$NEW"); ESPDEV=$(blkid -L KESTRELESP)
[ -b "$NEWDEV" ] && [ -b "$ESPDEV" ] || die "slot/ESP device missing"
[ "$NEWDEV" != "$ACTDEV" ] || die "target equals active slot"
D1=$(lsblk -no PKNAME "$NEWDEV"); D2=$(lsblk -no PKNAME "$ESPDEV"); D3=$(lsblk -no PKNAME "$ACTDEV")
[ "$D1" = "$D2" ] && [ "$D1" = "$D3" ] || die "slots and ESP are not on the same disk"
is_vm_disk "/dev/$D1" || die "/dev/$D1 is not a VM/loop disk; refusing"
findmnt -n "$NEWDEV" >/dev/null && die "inactive slot is mounted; refusing"
W=$(mktemp -d)
cleanup(){ set +e; umount "$W/new" 2>/dev/null; umount "$W/esp" 2>/dev/null; rm -rf "$W"; }  # on failure the target slot has no boot entry, so the old slot stays the default
trap cleanup EXIT
mkdir -p "$W/new" "$W/esp"
mount "$ESPDEV" "$W/esp"
ENT=$W/esp/loader/entries
[ -f "$ENT/kestrel-$ACT.conf" ] || die "ESP lacks kestrel-$ACT.conf; refusing"
# 1. Retire the target slot's entries first: nothing may boot a half-written slot. The ACT entry is never touched.
rm -f "$ENT/kestrel-$NEW.conf" "$ENT"/kestrel-"$NEW"+*.conf
sync
# 2. Write the root image into the inactive slot (device verified above, not re-resolved by label)
mkfs.ext4 -qF -L "root$NEW" "$NEWDEV"
mount "$NEWDEV" "$W/new"
tar --zstd -xpf "$IMG" -C "$W/new" --numeric-owner
# Required mountpoints must survive read-only root boot, even if the image omitted runtime directories.
install -d -m 755 "$W/new/run" "$W/new/dev" "$W/new/proc" "$W/new/sys" "$W/new/var" "$W/new/home"
install -d -m 1777 "$W/new/tmp"
find "$W/new/usr/local/bin" "$W/new/usr/local/lib/kestrel" -maxdepth 1 -type f -name "kestrel-*" -exec chmod 755 {} +
find "$W/new/usr/local/lib/kestrel" -maxdepth 1 -type f -name "*.sh" -exec chmod 755 {} +
chown -R root:root "$W/new/usr/local/bin" "$W/new/usr/local/lib/kestrel"
[ -f "$W/new/boot/vmlinuz-linux" ] && [ -f "$W/new/boot/initramfs-linux.img" ] || die "image lacks kernel/initramfs (staged under /boot)"
mkdir -p "$W/esp/$NEW"
cp "$W/new/boot/vmlinuz-linux" "$W/new/boot/initramfs-linux.img" "$W/esp/$NEW/"
rm -rf "$W/new/boot"; mkdir -p "$W/new/boot"       # /boot in the root is the ESP mountpoint
sync
# 3. Arm: new entry with 3 boot tries and a version higher than every existing entry. Default is the glob
#    "kestrel-*" (loader.conf), so sd-boot picks the highest version that still has tries left and falls back
#    to the old known-good entry when the counter hits +0. No EFI-variable default is used, so this does not
#    depend on persistent NVRAM beyond the LoaderBootCountPath variable sd-boot itself manages.
MAXV=$(grep -h '^version ' "$ENT"/kestrel-*.conf 2>/dev/null | awk '{print $2}' | sort -n | tail -1)
NEWV=$(( ${MAXV:-0} + 1 ))
cat > "$ENT/kestrel-$NEW+3.conf" <<L
title Kestrel OS ($NEW)
sort-key kestrel
version $NEWV
linux /$NEW/vmlinuz-linux
initrd /$NEW/initramfs-linux.img
options root=LABEL=root$NEW ro quiet kestrel.slot=$NEW
L
grep -qx 'default kestrel-\*' "$W/esp/loader/loader.conf" || printf 'default kestrel-*\ntimeout 2\n' > "$W/esp/loader/loader.conf"
sync
echo "Slot $NEW written (version $NEWV, 3 tries). Known-good fallback: slot $ACT (untouched). Reboot to test."
echo "Success path: kestrel-health.service passes -> systemd-bless-boot renames the entry to kestrel-$NEW.conf."
