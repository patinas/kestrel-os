#!/usr/bin/env bash
# One file when the ISO is under 2 GiB (GitHub release asset limit), else split into 1900M parts.
. "$(dirname "$0")/env.sh"
D=$CI_DIR/delivery; rm -rf "$D"; mkdir -p "$D"; name=$(basename "$ISO")
LIMIT=2147483648
size=$(stat -c %s "$ISO")
cp "$ISO" "$D/$name"
cd "$D"
sha256sum "$name" | tee SHA256SUMS.iso
if [ "$size" -lt "$LIMIT" ]; then
  mode=single
  [ "$(stat -c %s "$name")" -lt "$LIMIT" ]
  echo single > MODE
  verdict="Single file, $size bytes, under the 2 GiB asset limit."
else
  mode=split
  rm -f "$name"
  split -b 1900M -d -a 2 "$ISO" "$name.part"
  sha256sum "$name".part[0-9][0-9] | tee SHA256SUMS.parts
  original=$(sha256sum "$ISO" | cut -d' ' -f1)
  joined=$(cat "$name".part[0-9][0-9] | sha256sum | cut -d' ' -f1)
  [ "$original" = "$joined" ]
  for f in "$name".part[0-9][0-9]; do [ "$(stat -c %s "$f")" -lt "$LIMIT" ]; done
  echo split > MODE
  verdict="ISO is $size bytes (over 2 GiB), split into parts; reassembly checksum matches."
fi
{ echo '## Candidate delivery verification'; echo "Source: $GITHUB_SHA"; echo "Mode: $mode"; echo "ISO bytes: $size"; echo '```'; cat SHA256SUMS.iso; [ ! -f SHA256SUMS.parts ] || cat SHA256SUMS.parts; echo '```'; echo "$verdict Runner-local only until the draft pre-release step."; } | tee -a "$GITHUB_STEP_SUMMARY"
