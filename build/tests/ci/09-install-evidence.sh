#!/usr/bin/env bash
# Boot the freshly installed qcow2 disk-only over UEFI and capture screenshot evidence that the
# installed system reaches the shell. Readiness is the guest shell server's /status endpoint, not a timer.
. "$(dirname "$0")/env.sh"
[ "$ACCEL" = kvm ] || { echo 'KVM required'; exit 1; }
vars=$(find /usr/share/OVMF /usr/share/edk2 -type f \( -name 'OVMF_VARS_4M.fd' -o -name 'OVMF_VARS.fd' \) 2>/dev/null | head -1)
[ -n "$vars" ] || { echo "OVMF vars not found"; exit 1; }
cp "$vars" "$VM/INSTALL_VARS.fd"
qemu-system-x86_64 -machine q35,accel=kvm -cpu max -m 4096 -smp 4 \
 -drive if=pflash,format=raw,readonly=on,file="$(cat "$VM/ovmf-code")" \
 -drive if=pflash,format=raw,file="$VM/INSTALL_VARS.fd" \
 -drive if=none,id=testdisk,format=qcow2,file="$VM/disk.qcow2" -device virtio-blk-pci,drive=testdisk,serial=KESTREL_TEST_ONLY \
 -boot c -vga virtio -device virtio-rng-pci \
 -netdev user,id=n,hostfwd=tcp:127.0.0.1:18766-:8765 -device virtio-net,netdev=n \
 -device virtio-serial-pci -chardev null,id=ci -device virtserialport,chardev=ci,name=kestrel-ci-check \
 -display none -serial "file:$VM/install-serial.log" -qmp "unix:$VM/install-qmp.sock,server=on,wait=off" &
pid=$!
trap 'kill "$pid" 2>/dev/null || true; wait "$pid" 2>/dev/null || true' EXIT
sleep 20
rc=0
python3 "$REPO/build/tests/ci/install-evidence.py" "$VM" || rc=$?
kill "$pid" 2>/dev/null || true; wait "$pid" 2>/dev/null || true
for image in "$VM"/install-*.ppm; do
 name=$(basename "$image" .ppm)
 convert "$image" "$VM/$name.png"
 echo "INSTALL_EVIDENCE_BEGIN $name.png"
 base64 -w 100 "$VM/$name.png"
 echo "INSTALL_EVIDENCE_END $name.png"
done
# Human visual gate: screenshots must show the installed shell, not the live ISO.
echo 'Installed-disk boot screenshots captured. Visual inspection required before reporting install success.' | tee -a "$GITHUB_STEP_SUMMARY"
exit "$rc"
