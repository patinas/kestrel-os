# Sourced by the CI step scripts. CI_DIR is chosen in 00-host.sh and exported through $GITHUB_ENV.
set -Eeuo pipefail
: "${CI_DIR:?CI_DIR not set; run 00-host.sh first}"
REPO=${GITHUB_WORKSPACE:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)}
B=$CI_DIR/build            # working copy of repo/build, shared read-only with the guest over 9p
VM=$CI_DIR/vm              # qcow2, OVMF vars, serial logs (not shared)
ACCEL=${ACCEL:-tcg}
say(){ printf '\n=== %s ===\n' "$*"; }
