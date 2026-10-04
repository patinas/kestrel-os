#!/usr/bin/env bash
set -euo pipefail
sleep 150
cat /proc/cmdline
findmnt -no SOURCE,LABEL,OPTIONS /
pacman -Q steam gamescope minisign nvidia-open
ls -l /usr/local/lib/kestrel
systemctl --no-pager status kestrel-health.service boot-complete.target systemd-bless-boot.service || true
journalctl -b --no-pager -u kestrel-health.service -u systemd-bless-boot.service
ls -l /boot/loader/entries
bootctl status --no-pager || true
pgrep -a labwc; pgrep -af chrome | head -10
