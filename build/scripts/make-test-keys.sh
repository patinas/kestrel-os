#!/usr/bin/env bash
# TEST-ONLY minisign key pair for update tests (unencrypted secret key). Never use for releases.
set -euo pipefail
cd "$(dirname "$0")/.."; mkdir -p out/test-keys
[ -f out/test-keys/test.pub ] || minisign -G -W -p out/test-keys/test.pub -s out/test-keys/test.key -f
echo "public key: out/test-keys/test.pub (pass as KESTREL_UPDATE_PUB to install.sh)"
