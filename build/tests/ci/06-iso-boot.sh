#!/usr/bin/env bash
# Real UEFI ISO boot, no external kernel/initramfs, no writable guest disk.
. "$(dirname "$0")/env.sh"
[ "$ACCEL" = kvm ] || { echo 'KVM required'; exit 1; }
mkdir -p "$VM"
code=$(find /usr/share/OVMF -name OVMF_CODE_4M.fd | head -1)
vars=$(find /usr/share/OVMF -name OVMF_VARS_4M.fd | head -1)
[ -s "$code" ] && [ -s "$vars" ]
cp "$vars" "$VM/ISO_VARS.fd"
qemu-system-x86_64 -machine q35,accel=kvm -cpu max -m 8192 -smp 4 \
 -drive if=pflash,format=raw,readonly=on,file="$code" \
 -drive if=pflash,format=raw,file="$VM/ISO_VARS.fd" \
 -cdrom "$ISO" -boot d -vga virtio -device virtio-rng-pci \
 -netdev user,id=n,hostfwd=tcp:127.0.0.1:18765-:8765 -device virtio-net,netdev=n -device ich9-intel-hda -audiodev driver=none,id=silent -device hda-duplex,audiodev=silent -display none \
 -device virtio-serial-pci -chardev null,id=ci -device virtserialport,chardev=ci,name=kestrel-ci-check \
 -serial "file:$VM/iso-serial.log" -qmp "unix:$VM/iso-qmp.sock,server=on,wait=off" &
pid=$!
trap 'kill "$pid" 2>/dev/null || true; wait "$pid" 2>/dev/null || true' EXIT
sleep 150
rc=0
python3 "$REPO/build/tests/ci/iso-evidence.py" "$VM" || rc=$?
kill "$pid" 2>/dev/null || true; wait "$pid" 2>/dev/null || true
for image in "$VM"/iso-*.ppm; do
 name=$(basename "$image" .ppm)
 convert "$image" "$VM/$name.png"
 echo "ISO_EVIDENCE_BEGIN $name.png"
 base64 -w 100 "$VM/$name.png"
 echo "ISO_EVIDENCE_END $name.png"
done
# Human visual gate: screenshots must show the shell and process diagnostics.
echo 'Firmware boot screenshots captured. Visual inspection required before reporting boot success.' | tee -a "$GITHUB_STEP_SUMMARY"

exit "$rc"
