# shared helpers
die(){ echo "ERROR: $*" >&2; exit 1; }
need_root(){ [ "$(id -u)" = 0 ] || die "run as root"; }
partname(){ case $1 in *nvme*|*mmcblk*|*loop*) echo "${1}p$2";; *) echo "$1$2";; esac; }
# VM-only guard: accept only QEMU/virtio/loop-file disks. Refuse anything else.
is_vm_disk(){
  [ "$(systemd-detect-virt --vm 2>/dev/null)" = qemu ] || return 1
  local d=${1#/dev/} serial
  [ -b "/dev/$d" ] || return 1
  case "$d" in vd*) ;; *) return 1;; esac
  serial=$(cat "/sys/block/$d/serial" 2>/dev/null || true)
  [ "$serial" = KESTREL_TEST_ONLY ]
}
# Disk that holds the currently running root/live medium
running_disk(){
  local src; src=$(findmnt -no SOURCE / 2>/dev/null || true)
  local live; live=$(findmnt -no SOURCE /run/archiso/bootmnt 2>/dev/null || true)
  for s in "$src" "$live"; do
    [ -b "$s" ] && lsblk -no PKNAME "$s" 2>/dev/null | head -1
  done
}
