#!/usr/bin/env bash
. "$(dirname "$0")/env.sh"
D=$CI_DIR/delivery; mkdir -p "$D"; name=$(basename "$ISO")
split -b 1900M -d -a 2 "$ISO" "$D/$name.part"
cd "$D"
sha256sum *.part* | tee SHA256SUMS.parts
sha256sum "$ISO" | sed "s|$ISO|$name|" | tee SHA256SUMS.iso
original=$(sha256sum "$ISO" | cut -d' ' -f1)
joined=$(cat *.part* | sha256sum | cut -d' ' -f1)
[ "$original" = "$joined" ]
for f in *.part*; do [ "$(stat -c %s "$f")" -lt 2147483648 ]; done
{ echo '## Candidate delivery verification'; echo "Source: $GITHUB_SHA"; echo "ISO bytes: $(stat -c %s "$ISO")"; echo '```'; cat SHA256SUMS.iso SHA256SUMS.parts; echo '```'; echo 'Split/reassembly matches. Runner-local bytes only; no release or artifacts uploaded.'; } | tee -a "$GITHUB_STEP_SUMMARY"
