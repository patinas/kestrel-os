#!/usr/bin/env bash
# Unit test of the optional screen-lock password helper. No VM, no root, no network.
set -euo pipefail
H="$(cd "$(dirname "$0")/../../profile/airootfs/usr/local/bin" && pwd)/kestrel-lock-check"
export KESTREL_LOCK_FILE="$(mktemp -d)/sub/lock.json"
ok(){ echo "PASS $1"; }; bad(){ echo "FAIL $1"; exit 1; }
"$H" enabled && bad "enabled before set" || ok "off by default"
printf 'wrong-pass' | "$H" check && bad "check passes with no file" || ok "no file fails closed"
printf 'short\n' | "$H" set && bad "short accepted" || ok "short password rejected"
printf 'correct horse\n' | "$H" set && ok "set" || bad "set"
[ "$(stat -c %a "$KESTREL_LOCK_FILE")" = 600 ] && ok "file mode 600" || bad "file mode"
grep -q 'correct horse' "$KESTREL_LOCK_FILE" && bad "plaintext stored" || ok "hash only"
printf 'correct horse' | "$H" check && ok "right password" || bad "right password"
printf 'wrong horse' | "$H" check && bad "wrong accepted" || ok "wrong rejected"
printf 'another long one\n' | "$H" set && bad "change without current" || ok "change needs current"
printf 'another long one\nwrong horse' | "$H" set && bad "change with wrong current" || ok "change rejects wrong current"
printf 'another long one\ncorrect horse' | "$H" set && ok "change" || bad "change"
printf 'correct horse' | "$H" check && bad "old password still works" || ok "old password dead"
printf 'wrong horse' | "$H" clear && bad "clear wrong" || ok "clear needs current"
printf 'another long one' | "$H" clear && ok "clear" || bad "clear"
"$H" enabled && bad "enabled after clear" || ok "off after clear"
echo "lock-unit: all passed"
