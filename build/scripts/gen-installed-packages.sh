#!/usr/bin/env bash
# Installed package set = packages.x86_64 minus packages.live-only.txt. Run after editing either list.
# Use --check to fail (exit 1) when the committed overlay list is stale.
set -euo pipefail
cd "$(dirname "$0")/../profile"
OUT=airootfs/usr/share/kestrel/packages.installed.txt
TMP=$(mktemp)
grep -vE '^\s*(#|$)' packages.x86_64 | sort -u | comm -23 - <(grep -vE '^\s*(#|$)' packages.live-only.txt | sort -u) > "$TMP"
for need in base linux linux-firmware mkinitcpio networkmanager labwc waybar rpm-tools gnupg curl nss gtk3 minisign rsync; do grep -qx "$need" "$TMP" || { echo "missing required package $need" >&2; exit 1; }; done
if [ "${1:-}" = --check ]; then diff -u "$OUT" "$TMP" >/dev/null || { echo "stale $OUT; run scripts/gen-installed-packages.sh" >&2; exit 1; }; else mv "$TMP" "$OUT"; fi
