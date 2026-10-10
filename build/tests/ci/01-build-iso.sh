#!/usr/bin/env bash
# Build the live ISO from the checked-out source in an Arch container, workspace on $CI_DIR.
. "$(dirname "$0")/env.sh"
mkdir -p "$B"
rsync -a --delete --exclude out --exclude work --exclude cache "$REPO/build/" "$B/"
# Test observer is injected only into the disposable browser test copy, never the repo profile.
if [ "${KESTREL_UI_PROBE:-0}" = 1 ]; then
 install -Dm755 "$REPO/build/tests/ci/test-media-player.py" "$B/profile/airootfs/usr/local/lib/kestrel-ci/test-media-player.py"
 install -Dm755 "$REPO/build/tests/ci/guest-ui-probe.py" "$B/profile/airootfs/usr/local/lib/kestrel-ci/guest-ui-probe.py"
 mkdir -p "$B/profile/airootfs/etc/systemd/system/multi-user.target.wants"
 cat > "$B/profile/airootfs/etc/systemd/system/kestrel-ci-ui-probe.service" <<'SERVICE'
[Unit]
ConditionPathExists=/dev/virtio-ports/kestrel-ci-check
[Service]
StandardOutput=journal
StandardError=journal
ExecStart=/usr/bin/python3 /usr/local/lib/kestrel-ci/guest-ui-probe.py
[Install]
WantedBy=multi-user.target
SERVICE
 ln -s ../kestrel-ci-ui-probe.service "$B/profile/airootfs/etc/systemd/system/multi-user.target.wants/kestrel-ci-ui-probe.service"
fi
# Normalise modes without following symlinks (regular files only).
find "$B/profile/airootfs/usr/local/bin" "$B/profile/airootfs/usr/local/lib/kestrel" -type f -exec chmod 755 {} +
find "$B/scripts" "$B/tests" -type f -name '*.sh' -exec chmod 755 {} +
"$B/scripts/gen-installed-packages.sh" --check
mkdir -p "$B/out" "$B/work" "$B/cache"
# Hosted runners are not the shared test host: drop the local CPU/RAM/priority throttles from the build script copy.
sed -e 's/ --cpus=1 --memory=3g --memory-swap=3g//' -e '/renice 15/d' -e '/ionice -c 3/d' "$REPO/build/scripts/build.sh" > "$B/scripts/build.ci.sh"
chmod 755 "$B/scripts/build.ci.sh"
( cd "$B" && sudo ./scripts/build.ci.sh ) > "$CI_DIR/build.log" 2>&1 || { echo "::error::ISO build failed"; tail -n 200 "$CI_DIR/build.log"; exit 1; }
tail -n 25 "$CI_DIR/build.log"
ls -l "$B/out"
ISO=$(ls "$B"/out/kestrel-os-*.iso | head -1); [ -f "$ISO" ] || { echo "no ISO produced"; exit 1; }
echo "ISO=$ISO" >> "$GITHUB_ENV"
sha256sum "$ISO"
sudo rm -rf "$B/work" "$B/cache"; sudo chown -R "$(id -u):$(id -g)" "$B"
df -h "$CI_DIR"
