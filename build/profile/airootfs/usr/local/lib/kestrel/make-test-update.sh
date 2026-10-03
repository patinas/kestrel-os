#!/usr/bin/env bash
# Run INSIDE an installed Kestrel VM as root: packs the running root slot + its kernel into a signed update.
# Usage: make-test-update.sh <secret-key> <out-dir>   -> <out-dir>/root.tar.zst and root.tar.zst.minisig
set -Eeuo pipefail
. "$(dirname "$0")/lib.sh" 2>/dev/null || . /usr/local/lib/kestrel/lib.sh
need_root
KEY=${1:?test secret key}; OUT=${2:?out dir}; mkdir -p "$OUT"
ACT=$(sed -n 's/.*root=LABEL=root\([AB]\).*/\1/p' /proc/cmdline); [ -n "$ACT" ] || die "no active slot"
ls /boot >/dev/null 2>&1; [ -f "/boot/$ACT/vmlinuz-linux" ] || die "no kernel for slot $ACT on the ESP"
# Stream directly onto the data partition; do not stage a full uncompressed root.
# One filesystem excludes writable data and runtime mounts. Exact-name transforms affect only staged kernels.
tar --one-file-system --numeric-owner -cpf - -C / --exclude='./tmp/*' --exclude='./run/*' . \
  --transform='s,^vmlinuz-linux$,./boot/vmlinuz-linux,;s,^initramfs-linux.img$,./boot/initramfs-linux.img,' \
  -C "/boot/$ACT" vmlinuz-linux initramfs-linux.img | zstd -q -T1 -f -o "$OUT/root.tar.zst"
tar --zstd -tf "$OUT/root.tar.zst" | grep -E '^./boot/(vmlinuz-linux|initramfs-linux.img)$'
minisign -S -s "$KEY" -m "$OUT/root.tar.zst" -x "$OUT/root.tar.zst.minisig" -t "kestrel test update from slot $ACT" -f 2>/dev/null || minisign -S -W -s "$KEY" -m "$OUT/root.tar.zst" -x "$OUT/root.tar.zst.minisig"
ls -l "$OUT"
