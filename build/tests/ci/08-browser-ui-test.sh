#!/usr/bin/env bash
# One-user, disposable Kestrel UI test. Never a general desktop service.
. "$(dirname "$0")/env.sh"
[ "$ACCEL" = kvm ] || { echo 'KVM required'; exit 1; }
sudo apt-get install -y --no-install-recommends novnc websockify imagemagick fonts-dejavu-core python3-websocket
curl -fsSL https://github.com/cloudflare/cloudflared/releases/download/2026.9.3/cloudflared-linux-amd64 -o "$CI_DIR/cloudflared"
echo "77e26d8d900e0b8469f416239d14b5f296525fdf79fee6f511ef55609e3fbac2  $CI_DIR/cloudflared" | sha256sum -c -
chmod 755 "$CI_DIR/cloudflared"
"$CI_DIR/cloudflared" tunnel --help | grep -q -- '--allowed-mail'
mkdir -p "$VM"
code=$(find /usr/share/OVMF -name OVMF_CODE_4M.fd | head -1)
vars=$(find /usr/share/OVMF -name OVMF_VARS_4M.fd | head -1)
[ -s "$code" ] && [ -s "$vars" ]; cp "$vars" "$VM/UI_VARS.fd"
qemu-system-x86_64 -machine q35,accel=kvm -cpu max -m 8192 -smp 4 \
 -drive if=pflash,format=raw,readonly=on,file="$code" \
 -drive if=pflash,format=raw,file="$VM/UI_VARS.fd" \
 -cdrom "$ISO" -boot d -vga virtio -device virtio-rng-pci \
 -netdev user,id=n,hostfwd=tcp:127.0.0.1:18765-:8765,hostfwd=tcp:127.0.0.1:19222-:9233 -device virtio-net,netdev=n \
 -device ich9-intel-hda -audiodev driver=none,id=silent -device hda-duplex,audiodev=silent \
 -device virtio-serial-pci -chardev null,id=ci -device virtserialport,chardev=ci,name=kestrel-ci-check -vnc 127.0.0.1:1 -display none -serial "file:$VM/ui-serial.log" -qmp "unix:$VM/ui-qmp.sock,server=on,wait=off" &
qemu_pid=$!
trap 'kill "$qemu_pid" 2>/dev/null || true' EXIT
test_status=0
python3 "$REPO/build/tests/ci/window-controls-evidence.py" "$VM" || test_status=$?
for name in maximized-urlbar launcher-grid click-launcher-search quick-settings click-quick-before-all click-all-settings-result click-network click-advanced-off click-final-desktop; do
 image="$VM/ui-$name.ppm"
 [ -f "$image" ] || continue
 convert "$image" -quality 48 "$VM/ui-$name.jpg"
 echo "UI_EVIDENCE_BEGIN ui-$name.jpg"
 base64 -w 800 "$VM/ui-$name.jpg"
 echo "UI_EVIDENCE_END ui-$name.jpg"
done
[ "$test_status" = 0 ] || { echo "Click test failed; screenshots above are diagnostic, not a pass"; exit "$test_status"; }
websockify --web /usr/share/novnc 127.0.0.1:6080 127.0.0.1:5901 > "$CI_DIR/novnc.log" 2>&1 &
web_pid=$!
# Cloudflare email PIN protects HTTP AND WebSocket before they reach loopback.
# Fail closed if the installed client cannot configure protected Quick Tunnels.
"$CI_DIR/cloudflared" tunnel --url http://127.0.0.1:6080 --allowed-mail andreas.patinas@gmail.com --no-autoupdate > "$CI_DIR/tunnel.log" 2>&1 &
tunnel_pid=$!
cleanup(){ kill "$tunnel_pid" "$web_pid" "$qemu_pid" 2>/dev/null || true; wait 2>/dev/null || true; }
trap cleanup EXIT
for i in $(seq 1 60); do
 kill -0 "$tunnel_pid"; kill -0 "$web_pid"; kill -0 "$qemu_pid"
 url=$(grep -oE 'https://[a-z0-9-]+\.trycloudflare\.com' "$CI_DIR/tunnel.log" | head -1 || true)
 if [ -n "$url" ]; then break; fi
 sleep 2
done
[ -n "${url:-}" ] || { tail -40 "$CI_DIR/tunnel.log"; exit 1; }
echo "KESTREL_UI_TEST_URL=$url/vnc.html?autoconnect=true&resize=scale"
echo "One user only. Email PIN gate: andreas.patinas@gmail.com. Disposable test build; no disks, audio forwarding, saved data or release claim. Session expires 60 minutes after tunnel startup." >> "$GITHUB_STEP_SUMMARY"
echo "[$url]($url/vnc.html?autoconnect=true&resize=scale)" >> "$GITHUB_STEP_SUMMARY"
for i in $(seq 1 360); do
 kill -0 "$tunnel_pid"; kill -0 "$web_pid"; kill -0 "$qemu_pid"
 sleep 10
done
