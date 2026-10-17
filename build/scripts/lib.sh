# shared helpers
die(){ echo "ERROR: $*" >&2; exit 1; }
need_root(){ [ "$(id -u)" = 0 ] || die "run as root"; }
partname(){ case $1 in *nvme*|*mmcblk*|*loop*) echo "${1}p$2";; *) echo "$1$2";; esac; }
# Disk that holds the currently running root/live medium
running_disk(){
  local src; src=$(findmnt -no SOURCE / 2>/dev/null || true)
  local live; live=$(findmnt -no SOURCE /run/archiso/bootmnt 2>/dev/null || true)
  for s in "$src" "$live"; do
    [ -b "$s" ] && lsblk -no PKNAME "$s" 2>/dev/null | head -1
  done
}
# Whole disks that may be offered as install targets: TYPE=disk (excludes partitions,
# loop and rom devices) and not the disk hosting the running live system.
candidate_disks(){
  local run; run=$(running_disk)
  lsblk -dn -o NAME,TYPE | awk -v run="$run" '$2=="disk" && $1!=run {print $1}'
}
# Interactive disk pick. Prints the chosen /dev path on stdout, prompts on stderr.
select_disk(){
  local names; names=$(candidate_disks) || true
  [ -n "$names" ] || { echo "no installable disks found" >&2; return 1; }
  echo "Available disks (the live medium is excluded):" >&2
  lsblk -d -o NAME,SIZE,MODEL,TRAN $(printf '/dev/%s ' $names) >&2
  local pick
  printf 'Install to which disk? Type its NAME exactly (e.g. %s): ' "$(echo "$names" | head -1)" >&2
  read -r pick || return 1
  printf '%s\n' "$names" | grep -qx "$pick" || { echo "$pick is not an offered disk" >&2; return 1; }
  echo "/dev/$pick"
}
# Refuse anything that is not a safe whole-disk target. Keeps a log line for CI evidence.
check_target_disk(){
  local dev=$1 d model size virt
  virt=$(systemd-detect-virt --vm 2>/dev/null || true)
  [ -b "$dev" ] || die "$dev is not a block device"
  d=$(basename "$dev")
  [ "$(lsblk -dn -o TYPE "$dev" 2>/dev/null)" = disk ] || die "$dev is not a whole disk (partition, loop or rom); refusing"
  [ "$d" != "$(running_disk)" ] || die "$dev holds the running system; refusing"
  if lsblk -no MOUNTPOINTS "$dev" | grep -q .; then die "$dev has mounted partitions; refusing"; fi
  model=$(lsblk -dn -o MODEL "$dev" 2>/dev/null | sed 's/ *$//')
  size=$(lsblk -dn -o SIZE "$dev" 2>/dev/null)
  echo "target check: virtualization=${virt:-none} disk=$dev model='${model:-unknown}' size=${size:-?}" >&2
}
