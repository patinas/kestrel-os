#!/usr/bin/env bash
# Test signing key, live kernel/initramfs, 40 GiB thin qcow2, persistent OVMF vars, wait-time hint for guest jobs.
. "$(dirname "$0")/env.sh"
mkdir -p "$VM" "$B/out/test-keys"
# Disposable TEST-ONLY key pair (never committed, never uploaded).
rm -f "$B/out/test-keys/test.pub" "$B/out/test-keys/test.key"
minisign -G -W -f -p "$B/out/test-keys/test.pub" -s "$B/out/test-keys/test.key"
ISO=${ISO:?}
xorriso -osirrox on -indev "$ISO" -extract /kestrel/boot/x86_64/vmlinuz-linux "$VM/vmlinuz" -extract /kestrel/boot/x86_64/initramfs-linux.img "$VM/initramfs" 2>&1 | tail -3
[ -s "$VM/vmlinuz" ] && [ -s "$VM/initramfs" ] || { xorriso -indev "$ISO" -find / -name 'vmlinuz*' 2>/dev/null | head; echo "kernel extract failed"; exit 1; }
LABEL=$(xorriso -indev "$ISO" -pvd_info 2>&1 | sed -n 's/^Volume Id *: *//p' | head -1)
[ -n "$LABEL" ] || { echo "no ISO volume id"; exit 1; }
LABEL=${LABEL#\'}; LABEL=${LABEL%\'}
echo "$LABEL" > "$VM/iso-label"; echo "ISO label: $LABEL"
qemu-img create -f qcow2 "$VM/disk.qcow2" 40G
code=$(find /usr/share/OVMF /usr/share/edk2 -type f \( -name 'OVMF_CODE_4M.fd' -o -name 'OVMF_CODE.fd' \) 2>/dev/null | head -1 || true)
vars=$(find /usr/share/OVMF /usr/share/edk2 -type f \( -name 'OVMF_VARS_4M.fd' -o -name 'OVMF_VARS.fd' \) 2>/dev/null | head -1 || true)
[ -n "$code" ] && [ -n "$vars" ] || { echo "OVMF not found"; exit 1; }
echo "$code" > "$VM/ovmf-code"; cp "$vars" "$VM/OVMF_VARS.fd"
# Guest jobs read their time budget (seconds) from the share.
if [ "$ACCEL" = kvm ]; then echo 1500 > "$B/ci-wait"; else echo 6000 > "$B/ci-wait"; fi
printf "%s\n" "${KESTREL_CI_LAUNCHERS:-none}" > "$B/ci-launchers"
df -h "$CI_DIR"
