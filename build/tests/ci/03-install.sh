#!/usr/bin/env bash
# Boot the live ISO with the repo build dir over read-only 9p and run jobs/ci-install.sh (full-package installer).
. "$(dirname "$0")/env.sh"; . "$(dirname "$0")/qemu.sh"
ISO=${ISO:?}; LABEL=$(cat "$VM/iso-label")
APPEND="archisobasedir=kestrel archisolabel=$LABEL console=tty0 console=ttyS0 systemd.run=\"/usr/bin/mkdir -p /run/kestrelshare\" systemd.run=\"/usr/bin/mount -t 9p -o trans=virtio,version=9p2000.L,ro kestreltest /run/kestrelshare\" systemd.run=\"/usr/bin/bash /run/kestrelshare/tests/jobs/ci-install.sh\" systemd.run_success_action=none systemd.run_failure_action=none"
tmo=7200; [ "$ACCEL" = kvm ] || tmo=18000
rc=0
qemu_launch "$VM/serial-install.log" "$tmo" -cdrom "$ISO" -kernel "$VM/vmlinuz" -initrd "$VM/initramfs" -append "$APPEND" || rc=$?
grep -E 'root slot usage|Installed to|CI_INSTALL_DONE|CI_FAIL|ERROR' "$VM/serial-install.log" | tail -20 || true
if [ "$rc" -ne 0 ] || ! grep -q '^CI_INSTALL_DONE' "$VM/serial-install.log"; then
  echo "::error::install did not complete (rc=$rc)"; tail -n 120 "$VM/serial-install.log"; exit 1
fi
rm -f "$ISO"; df -h "$CI_DIR"
