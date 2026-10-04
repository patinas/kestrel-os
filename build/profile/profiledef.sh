#!/usr/bin/env bash
# shellcheck disable=SC2034
iso_name="kestrel-os"
iso_label="KESTREL_$(date +%Y%m)"
iso_publisher="Kestrel OS <https://github.com/patinas/kestrel-os>"
iso_application="Kestrel OS live image"
iso_version="$(date +%Y.%m.%d)"
install_dir="kestrel"
buildmodes=('iso')
bootmodes=('uefi-x64.systemd-boot.esp' 'uefi-x64.systemd-boot.eltorito')
arch="x86_64"
pacman_conf="pacman.conf"
airootfs_image_type="squashfs"
airootfs_image_tool_options=('-comp' 'zstd' '-Xcompression-level' '3' '-b' '1M')
declare -A file_permissions=(
  ["/usr/local/bin/kestrel-chrome-setup"]="0:0:755"
  ["/usr/local/bin/kestrel-mode"]="0:0:755"
  ["/usr/local/bin/kestrel-gaming-session"]="0:0:755"
  ["/usr/local/bin/kestrel-gpu-select"]="0:0:755"
  ["/usr/local/lib/kestrel/install.sh"]="0:0:755"
  ["/usr/local/lib/kestrel/update.sh"]="0:0:755"
  ["/usr/local/lib/kestrel/health-check.sh"]="0:0:755"
  ["/usr/local/lib/kestrel/make-test-update.sh"]="0:0:755"
  ["/usr/local/bin/kestrel-session"]="0:0:755"
  ["/usr/local/bin/kestrel-firstboot"]="0:0:755"
)
