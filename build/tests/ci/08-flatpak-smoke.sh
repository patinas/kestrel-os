#!/usr/bin/env bash
# Flatpak runtime smoke in a real UEFI boot of the candidate ISO. Runner-local
# evidence only (screenshots in the step log); no release, no upload.
. "$(dirname "$0")/env.sh"
[ "$ACCEL" = kvm ] || { echo 'KVM required'; exit 1; }
mkdir -p "$VM"
code=$(find /usr/share/OVMF -name OVMF_CODE_4M.fd | head -1)
vars=$(find /usr/share/OVMF -name OVMF_VARS_4M.fd | head -1)
[ -s "$code" ] && [ -s "$vars" ]
cp "$vars" "$VM/FLATPAK_VARS.fd"
qemu-system-x86_64 -machine q35,accel=kvm -cpu max -m 8192 -smp 4 \
 -drive if=pflash,format=raw,readonly=on,file="$code" \
 -drive if=pflash,format=raw,file="$VM/FLATPAK_VARS.fd" \
 -cdrom "$ISO" -boot d -vga virtio -device virtio-rng-pci \
 -device virtio-serial-pci -chardev null,id=ci -device virtserialport,chardev=ci,name=kestrel-ci-check \
 -netdev user,id=n,hostfwd=tcp:127.0.0.1:18765-:8765 -device virtio-net,netdev=n -device ich9-intel-hda -audiodev driver=none,id=silent -device hda-duplex,audiodev=silent -display none \
 -serial "file:$VM/flatpak-serial.log" -qmp "unix:$VM/flatpak-qmp.sock,server=on,wait=off" &
pid=$!
trap 'kill "$pid" 2>/dev/null || true; wait "$pid" 2>/dev/null || true' EXIT
sleep 150
rc=0
python3 "$REPO/build/tests/ci/flatpak-evidence.py" "$VM" || rc=$?
kill "$pid" 2>/dev/null || true; wait "$pid" 2>/dev/null || true
# The guest serial console is the only record of first boot (chrome-setup
# prompt, Chrome download progress or errors). Dump it so a failure is
# diagnosable from the step log instead of needing a rerun.
echo '--- flatpak-serial.log (tail 200 lines) ---'
tail -n 200 "$VM/flatpak-serial.log" 2>/dev/null || echo '(no serial log captured)'
echo '--- end flatpak-serial.log ---'
shopt -s nullglob
for image in "$VM"/flatpak-*.ppm; do
 name=$(basename "$image" .ppm)
 convert "$image" "$VM/$name.png"
 echo "FLATPAK_EVIDENCE_BEGIN $name.png"
 base64 -w 100 "$VM/$name.png"
 echo "FLATPAK_EVIDENCE_END $name.png"
done
# Visual gate: SMOKE_RESULT=PASS must be visible, plus calculator window and
# launcher grid pixels, before runtime support is claimed.
echo 'Flatpak smoke screenshots captured. Visual inspection required before reporting runtime support.' | tee -a "$GITHUB_STEP_SUMMARY"
exit "$rc"
