#!/usr/bin/env bash
# Real UEFI ISO boot, no external kernel/initramfs, no writable guest disk.
. "$(dirname "$0")/env.sh"
[ "$ACCEL" = kvm ] || { echo 'KVM required'; exit 1; }
mkdir -p "$VM"
code=$(find /usr/share/OVMF -name OVMF_CODE_4M.fd | head -1)
vars=$(find /usr/share/OVMF -name OVMF_VARS_4M.fd | head -1)
[ -s "$code" ] && [ -s "$vars" ]
cp "$vars" "$VM/ISO_VARS.fd"
qemu-system-x86_64 -machine q35,accel=kvm -cpu max -m 4096 -smp 4 \
 -drive if=pflash,format=raw,readonly=on,file="$code" \
 -drive if=pflash,format=raw,file="$VM/ISO_VARS.fd" \
 -cdrom "$ISO" -boot d -vga virtio -device virtio-rng-pci \
 -netdev user,id=n -device virtio-net,netdev=n -display none \
 -serial "file:$VM/iso-serial.log" -qmp "unix:$VM/iso-qmp.sock,server=on,wait=off" &
pid=$!
trap 'kill "$pid" 2>/dev/null || true; wait "$pid" 2>/dev/null || true' EXIT
sleep 150
python3 "$REPO/build/tests/ci/iso-evidence.py" "$VM"
for name in iso-shell iso-console; do
 convert "$VM/$name.ppm" "$VM/$name.png"
 echo "ISO_EVIDENCE_BEGIN $name.png"
 base64 -w 100 "$VM/$name.png"
 echo "ISO_EVIDENCE_END $name.png"
done
# Human visual gate: screenshots must show the shell and process diagnostics.
echo 'Firmware boot screenshots captured. Visual inspection required before reporting boot success.' | tee -a "$GITHUB_STEP_SUMMARY"
