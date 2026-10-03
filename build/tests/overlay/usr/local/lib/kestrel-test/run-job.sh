#!/usr/bin/env bash
set -euo pipefail
virt=$(systemd-detect-virt --vm || true)
case "$virt" in qemu|kvm) ;; *) exit 1;; esac
grep -qi QEMU /sys/class/dmi/id/sys_vendor
[ "$(cat /sys/block/vda/serial)" = KESTREL_TEST_ONLY ]
mkdir -p /run/kestrel-test
mount -t 9p -o trans=virtio,version=9p2000.L,ro kestreltest /run/kestrel-test
job=$(sed -n 's/.*kestrel.job=\([a-zA-Z0-9_-]*\).*/\1/p' /proc/cmdline)
[ -n "$job" ] && [ -f "/run/kestrel-test/tests/jobs/$job.sh" ]
echo "KESTREL_TEST_START job=$job"
bash "/run/kestrel-test/tests/jobs/$job.sh"
echo "KESTREL_TEST_DONE job=$job"
