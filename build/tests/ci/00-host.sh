#!/usr/bin/env bash
# Free disk, enable /dev/kvm if the runner has it, install QEMU tooling, pick the work dir. No secrets used.
set -Eeuo pipefail
echo "--- before"; df -h / /mnt || true
# The hosted image carries large toolchains we do not need; removing them frees ~25-30 GB on /.
sudo rm -rf /usr/share/dotnet /usr/local/lib/android /opt/ghc /opt/hostedtoolcache/CodeQL /usr/local/share/boost 2>/dev/null || true
sudo docker image prune -af >/dev/null 2>&1 || true
echo "--- after cleanup"; df -h / /mnt || true
# Work dir: whichever of / and /mnt has more free space (the 14 GB-root case lands on /mnt).
free_root=$(df -Pk / | awk 'NR==2{print $4}'); free_mnt=$(df -Pk /mnt 2>/dev/null | awk 'NR==2{print $4}'); free_mnt=${free_mnt:-0}
if [ "$free_mnt" -gt "$free_root" ]; then base=/mnt; else base=/home/runner/work; fi
sudo mkdir -p "$base/kestrel-ci"; sudo chown -R "$(id -u):$(id -g)" "$base/kestrel-ci"
echo "CI_DIR=$base/kestrel-ci" >> "$GITHUB_ENV"
echo "work dir: $base/kestrel-ci (free KiB: root=$free_root mnt=$free_mnt)"
# Only grant the current runner account access to KVM, no persistent udev rule.
accel=tcg
if [ -e /dev/kvm ]; then
  sudo chown root:"$(id -g)" /dev/kvm
  sudo chmod 0660 /dev/kvm
  [ -r /dev/kvm ] && [ -w /dev/kvm ] && accel=kvm
fi
echo "ACCEL=$accel" >> "$GITHUB_ENV"
if [ "$accel" = tcg ]; then
  echo "::warning::/dev/kvm unavailable; falling back to TCG (slow)"
  [ "${KESTREL_CI_ALLOW_TCG:-true}" = true ] || { echo "::error::TCG not allowed by input"; exit 1; }
fi
sudo apt-get update -qq
sudo apt-get install -y --no-install-recommends qemu-system-x86 qemu-utils ovmf minisign xorriso zstd rsync python3
qemu-system-x86_64 --version | head -1; minisign -v 2>&1 | head -1 || true
