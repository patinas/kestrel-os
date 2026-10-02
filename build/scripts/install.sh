#!/usr/bin/env bash
# Kestrel installer, VM-ONLY. Usage: install.sh /dev/vdX   (run as root in the live ISO)
# GPT: 1 ESP 512M (kernels per slot: /A, /B) | 2 rootA 6G | 3 rootB 6G | 4 kdata (/var, /home)
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
cleanup(){ set +e; umount "$W/esp" 2>/dev/null; umount "$W/kd" 2>/dev/null; umount -R "$W/mnt" 2>/dev/null; umount -R "$T" 2>/dev/null; rm -rf "$W"; }
trap cleanup EXIT
P1=$(partname "$DEV" 1); P2=$(partname "$DEV" 2); P3=$(partname "$DEV" 3); P4=$(partname "$DEV" 4)
wipefs -a "$DEV" >/dev/null
parted -s "$DEV" mklabel gpt \
  mkpart ESP fat32 1MiB 513MiB set 1 esp on \
  mkpart rootA ext4 513MiB 6657MiB mkpart rootB ext4 6657MiB 12801MiB mkpart kdata ext4 12801MiB 100%
partprobe "$DEV"; udevadm settle
mkfs.fat -F32 -n KESTRELESP "$P1"; mkfs.ext4 -qF -L rootA "$P2"; mkfs.ext4 -qF -L rootB "$P3"; mkfs.ext4 -qF -L kdata "$P4"
# 1. Build the root tree once in a scratch dir on the live system's tmpfs/disk
mkdir -p "$T"; mount "$P2" "$T"
pacstrap -K "$T" base linux linux-firmware mkinitcpio sudo networkmanager bluez cage chromium mesa pipewire pipewire-pulse wireplumber noto-fonts
# 2. Kestrel overlay: shell, scripts, services, user
for p in usr/local/bin usr/share/kestrel etc/chromium etc/os-release etc/hostname etc/skel; do
  [ -e "$SRC/$p" ] && { mkdir -p "$T/$(dirname "$p")"; cp -a "$SRC/$p" "$T/$(dirname "$p")/"; }
done
mkdir -p "$T/etc/systemd/system/getty@tty1.service.d" "$T/etc/systemd/system/multi-user.target.wants"
for unit in kestrel-gpu-select.service kestrel-firstboot.service; do
  cp "$SRC/etc/systemd/system/$unit" "$T/etc/systemd/system/"
done
cp "$SRC/etc/systemd/system/getty@tty1.service.d/autologin.conf" "$T/etc/systemd/system/getty@tty1.service.d/"
ln -sfn /dev/null "$T/etc/systemd/system/systemd-firstboot.service"
printf 'LANG=en_US.UTF-8\n' > "$T/etc/locale.conf"
arch-chroot "$T" useradd -m -s /bin/bash -G wheel,video,audio,input kestrel
arch-chroot "$T" passwd -d kestrel
arch-chroot "$T" systemctl enable NetworkManager bluetooth kestrel-gpu-select.service kestrel-firstboot.service
# 3. fstab: root read-only, /var and /home on writable kdata
cat > "$T/etc/fstab" <<F
# root mounted ro by kernel cmdline
LABEL=KESTRELESP /boot vfat umask=0077,noauto,x-systemd.automount 0 2
LABEL=kdata /var  ext4 defaults 0 2
/var/home /home none bind,x-systemd.requires-mounts-for=/var 0 0
F
# Persist data dirs onto kdata on first populate
mkdir -p "$W/kd"; mount "$P4" "$W/kd"
cp -a "$T/var/." "$W/kd/"; mkdir -p "$W/kd/home"; cp -a "$T/home/kestrel" "$W/kd/home/"; umount "$W/kd"
rm -rf "$T/home/kestrel"; mkdir -p "$T/var/home"  # real data lives on kdata:/home, mounted at /var/home
# 4. Kernel per slot on the ESP; initramfs built into each slot's directory
mkdir -p "$W/esp"; mount "$P1" "$W/esp"; mkdir -p "$W/esp/A" "$W/esp/B" "$W/esp/loader/entries"
cp "$T/boot/vmlinuz-linux" "$W/esp/A/"; cp "$T/boot/initramfs-linux.img" "$W/esp/A/"
cp "$T/boot/vmlinuz-linux" "$W/esp/B/"; cp "$T/boot/initramfs-linux.img" "$W/esp/B/"
# 5. Populate slot B from slot A (identical tree)
mkdir -p "$W/mnt"; mount "$P3" "$W/mnt"; rsync -aHAX --exclude=/boot/* "$T"/ "$W/mnt"/; umount "$W/mnt"
for s in A B; do cat > "$W/esp/loader/entries/kestrel-$s.conf" <<L
title Kestrel OS ($s)
linux /$s/vmlinuz-linux
initrd /$s/initramfs-linux.img
options root=LABEL=root$s ro quiet kestrel.slot=$s
L
done
echo "default kestrel-A.conf" > "$W/esp/loader/loader.conf"; echo "timeout 2" >> "$W/esp/loader/loader.conf"
bootctl --esp-path="$W/esp" install || bootctl --esp-path="$W/esp" --no-variables install
sync; umount "$W/esp"
echo "Installed to $DEV. Slots A and B populated; default A."
