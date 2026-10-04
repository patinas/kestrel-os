#!/usr/bin/env bash
# Kestrel installer, VM-ONLY. Usage: install.sh /dev/vdX   (run as root in the live ISO)
# GPT: 1 ESP 512M (kernels per slot: /A, /B) | 2 rootA 12G | 3 rootB 12G | 4 kdata (/var, /home, rest of disk)
# Env: KESTREL_ROOT_GIB (default 12), KESTREL_UPDATE_PUB (path to a TEST-ONLY minisign public key to install)
set -Eeuo pipefail
. "$(dirname "$0")/lib.sh"
need_root
DEV=${1:?usage: install.sh /dev/vdX}
[ "${KESTREL_ALLOW_VM_INSTALL:-}" = yes ] || die "set KESTREL_ALLOW_VM_INSTALL=yes (VM-only installer)"
is_vm_disk "$DEV" || die "$DEV is not a recognised VM/loop disk; refusing"
[ "$(basename "$DEV")" != "$(running_disk)" ] || die "$DEV holds the running system; refusing"
if lsblk -no MOUNTPOINTS "$DEV" | grep -q .; then die "$DEV has mounted partitions; refusing"; fi
[ "${KESTREL_CONFIRM:-}" = "ERASE $DEV" ] || die "set KESTREL_CONFIRM='ERASE $DEV' to confirm"
SRC=${KESTREL_SRC_OVERLAY:-/}            # live root providing /usr/local, shell, services
W=$(mktemp -d); T=$W/target
cleanup(){ set +e; umount "$W/esp" 2>/dev/null; umount "$W/kd" 2>/dev/null; umount -R "$W/mnt" 2>/dev/null; umount -R "$T" 2>/dev/null; umount -l "$T" 2>/dev/null; rm -rf "$W"; }
trap cleanup EXIT
P1=$(partname "$DEV" 1); P2=$(partname "$DEV" 2); P3=$(partname "$DEV" 3); P4=$(partname "$DEV" 4)
ROOT_GIB=${KESTREL_ROOT_GIB:-12}
case $ROOT_GIB in ''|*[!0-9]*) die "KESTREL_ROOT_GIB must be an integer";; esac
DISK_GIB=$(( $(blockdev --getsize64 "$DEV") / 1073741824 ))
NEED=$(( 1 + 2*ROOT_GIB + 4 ))      # ESP + two roots + at least 4 GiB data
[ "$DISK_GIB" -ge "$NEED" ] || die "$DEV is ${DISK_GIB} GiB; need at least ${NEED} GiB (2 x ${ROOT_GIB} GiB roots + data)"
R1=513; R2=$(( R1 + ROOT_GIB*1024 )); R3=$(( R2 + ROOT_GIB*1024 ))
# Preflight before touching the disk: package list, pacman.conf (multilib + signatures), overlay files
PKGLIST="$SRC/usr/share/kestrel/packages.installed.txt"
[ -r "$PKGLIST" ] || die "missing $PKGLIST"
PKGS=$(grep -vE '^\s*(#|$)' "$PKGLIST" | sort -u | tr '\n' ' ')
[ -n "$PKGS" ] || die "empty package list"
PCONF=${KESTREL_PACMAN_CONF:-/etc/pacman.conf}
grep -Eq '^\[multilib\]' "$PCONF" || die "$PCONF has no [multilib] section"
grep -Eq '^SigLevel *= *Required' "$PCONF" || die "$PCONF does not require package signatures"
! grep -Eqi '^SigLevel.*(Never|TrustAll)' "$PCONF" || die "$PCONF weakens signature checks"
for f in usr/local/lib/kestrel/health-check.sh usr/local/lib/kestrel/update.sh usr/local/lib/kestrel/lib.sh etc/systemd/system/kestrel-health.service usr/share/kestrel/shell/index.html; do
  [ -e "$SRC/$f" ] || die "overlay file missing: $SRC/$f"
done
if [ -n "${KESTREL_UPDATE_PUB:-}" ]; then [ -r "$KESTREL_UPDATE_PUB" ] || die "KESTREL_UPDATE_PUB not readable"; fi
wipefs -a "$DEV" >/dev/null
parted -s "$DEV" mklabel gpt \
  mkpart ESP fat32 1MiB 513MiB set 1 esp on \
  mkpart rootA ext4 ${R1}MiB ${R2}MiB mkpart rootB ext4 ${R2}MiB ${R3}MiB mkpart kdata ext4 ${R3}MiB 100%
partprobe "$DEV"; udevadm settle
mkfs.fat -F32 -n KESTRELESP "$P1"; mkfs.ext4 -qF -L rootA "$P2"; mkfs.ext4 -qF -L rootB "$P3"; mkfs.ext4 -qF -L kdata "$P4"
# 1. Build the root tree once in a scratch dir on the live system's tmpfs/disk
mkdir -p "$T"; mount "$P2" "$T"
mkdir -p /etc/pacman.d
printf 'Server = https://geo.mirror.pkgbuild.com/$repo/os/$arch\n' > /etc/pacman.d/mirrorlist
pacman-key --init
pacman-key --populate archlinux
# one transaction, full authoritative list, signatures required, multilib enabled
# shellcheck disable=SC2086
pacstrap -C "$PCONF" "$T" $PKGS
cp "$PCONF" "$T/etc/pacman.conf"; cp /etc/pacman.d/mirrorlist "$T/etc/pacman.d/mirrorlist"
USED=$(df --output=pcent "$T" | tail -1 | tr -dc 0-9)
echo "root slot usage after install: ${USED}% of ${ROOT_GIB} GiB"
[ "$USED" -lt 85 ] || die "installed root uses ${USED}% of the slot; raise KESTREL_ROOT_GIB"
# 2. Kestrel overlay: shell, scripts, services, user
for p in usr/local/bin usr/local/lib/kestrel usr/share/kestrel etc/sudoers.d etc/os-release etc/hostname etc/skel; do
  [ -e "$SRC/$p" ] && { mkdir -p "$T/$(dirname "$p")"; cp -a "$SRC/$p" "$T/$(dirname "$p")/"; }
done
find "$T/usr/local/bin" -maxdepth 1 -type f -name "kestrel-*" -exec chmod 755 {} +
find "$T/usr/local/lib/kestrel" -maxdepth 1 -type f -name "*.sh" -exec chmod 755 {} +
chown -R root:root "$T/usr/local/bin" "$T/usr/local/lib/kestrel"
mkdir -p "$T/etc/systemd/system/getty@tty1.service.d" "$T/etc/systemd/system/multi-user.target.wants"
for unit in kestrel-gpu-select.service kestrel-firstboot.service kestrel-health.service; do
  cp "$SRC/etc/systemd/system/$unit" "$T/etc/systemd/system/"
done
cp "$SRC/etc/systemd/system/getty@tty1.service.d/autologin.conf" "$T/etc/systemd/system/getty@tty1.service.d/"
ln -sfn /dev/null "$T/etc/systemd/system/systemd-firstboot.service"
printf 'LANG=en_US.UTF-8\n' > "$T/etc/locale.conf"
arch-chroot "$T" useradd -m -s /bin/bash -G wheel,video,audio,input kestrel
arch-chroot "$T" passwd -d kestrel
arch-chroot "$T" systemctl enable NetworkManager bluetooth kestrel-gpu-select.service kestrel-firstboot.service kestrel-health.service
# kestrel-health.service is RequiredBy=boot-complete.target; verify the enablement link exists
[ -L "$T/etc/systemd/system/boot-complete.target.requires/kestrel-health.service" ] || die "health gate not enabled"
[ -L "$T/etc/systemd/system/multi-user.target.wants/kestrel-health.service" ] || die "health gate not enabled for counter-less boots"
# systemd-bless-boot is pulled in by its generator when the loader sets boot counting; make sure it is not masked
[ "$(readlink "$T/etc/systemd/system/systemd-bless-boot.service" 2>/dev/null)" != /dev/null ] || die "systemd-bless-boot masked"
# installed footer text (the live image says "alpha live image")
sed -i 's/alpha live image/Kestrel OS alpha \xc2\xb7 installed/' "$T/usr/share/kestrel/shell/index.html"
grep -q 'installed' "$T/usr/share/kestrel/shell/index.html" || die "footer not updated"
# updater: command + (test-only) public key
ln -sfn /usr/local/lib/kestrel/update.sh "$T/usr/local/bin/kestrel-update"
mkdir -p "$T/etc/kestrel"
if [ -n "${KESTREL_UPDATE_PUB:-}" ]; then
  install -m 644 "$KESTREL_UPDATE_PUB" "$T/etc/kestrel/update.pub"
  echo "TEST-ONLY key installed by installer; replace with a release key before any real use" > "$T/etc/kestrel/update.pub.TESTONLY"
fi
# Persist local sudo password without unlocking either root slot.
mkdir -p "$T/var/lib/kestrel"
cp "$T/etc/shadow" "$T/var/lib/kestrel/shadow"
chmod 600 "$T/var/lib/kestrel/shadow"
# 3. fstab: root read-only, /var and /home on writable kdata
cat > "$T/etc/fstab" <<F
# root mounted ro by kernel cmdline
LABEL=KESTRELESP /boot vfat umask=0077,noauto,x-systemd.automount 0 2
LABEL=kdata /var  ext4 defaults 0 2
/var/home /home none bind,x-systemd.requires-mounts-for=/var 0 0
/var/lib/kestrel/shadow /etc/shadow none bind,x-systemd.requires-mounts-for=/var 0 0
F
# Persist data dirs onto kdata on first populate
mkdir -p "$W/kd"; mount "$P4" "$W/kd"
cp -a "$T/var/." "$W/kd/"; mkdir -p "$W/kd/home"; cp -a "$T/home/kestrel" "$W/kd/home/"; umount "$W/kd"
rm -rf "$T/home/kestrel"; mkdir -p "$T/var/home"  # real data lives on kdata:/home, mounted at /var/home
# 4. Kernel per slot on the ESP; initramfs built into each slot's directory
mkdir -p "$W/esp"; mount -o umask=0077 "$P1" "$W/esp"; mkdir -p "$W/esp/A" "$W/esp/B" "$W/esp/loader/entries"
cp "$T/boot/vmlinuz-linux" "$W/esp/A/"; cp "$T/boot/initramfs-linux.img" "$W/esp/A/"
cp "$T/boot/vmlinuz-linux" "$W/esp/B/"; cp "$T/boot/initramfs-linux.img" "$W/esp/B/"
# 5. Populate slot B from slot A (identical tree)
mkdir -p "$W/mnt"; mount "$P3" "$W/mnt"; rsync -aHAX --exclude=/boot/* "$T"/ "$W/mnt"/; umount "$W/mnt"
# Boot assessment (systemd.io/AUTOMATIC_BOOT_ASSESSMENT): entries sorted by sort-key then version (highest first);
# an entry with a "+N" counter that reaches +0 sorts last, so the older known-good entry takes over.
# A starts as version 2 (default), B as version 1; both are counter-less = known good.
declare -A VER=([A]=2 [B]=1)
for s in A B; do cat > "$W/esp/loader/entries/kestrel-$s.conf" <<L
title Kestrel OS ($s)
sort-key kestrel
version ${VER[$s]}
linux /$s/vmlinuz-linux
initrd /$s/initramfs-linux.img
options root=LABEL=root$s ro quiet kestrel.slot=$s
L
done
printf 'default kestrel-*\ntimeout 2\n' > "$W/esp/loader/loader.conf"
bootctl --esp-path="$W/esp" install || bootctl --esp-path="$W/esp" --no-variables install
sync; umount "$W/esp"
echo "Installed to $DEV. Slots A and B populated; default A."
