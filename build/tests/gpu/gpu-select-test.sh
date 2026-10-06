#!/usr/bin/env bash
# Logic test for kestrel-gpu-select with stubbed lspci/modinfo/lsmod/modprobe/rmmod and a fake sysfs. No GPU needed.
# Proves the decision logic only; it does NOT prove real drivers load. Run: bash build/tests/gpu/gpu-select-test.sh
set -u
here=$(cd "$(dirname "$0")" && pwd); SEL="$here/../../profile/airootfs/usr/local/bin/kestrel-gpu-select"
fail=0
run() { # name lspci_ids("amd:1002:73bf nv:2684") nv_alias_ids nouveau_loaded modprobe_ok expected_stack expected_wlr
  local name=$1 cards=$2 nvalias=$3 nouv=$4 mpok=$5 exp=$6 expwlr=$7
  local t; t=$(mktemp -d); mkdir -p "$t/bin" "$t/run" "$t/sys/class/drm" "$t/persist"
  local lines="" i=0 first=1
  for c in $cards; do
    IFS=: read -r kind vend id <<<"$c"
    lines+="00:0$i.0 VGA compatible controller [0300]: Vendor [$vend:$id] (rev a1)\n"
    d="$t/sys/devices/pci0000:00/0000:00:0$i.0"; mkdir -p "$d"; echo "0x$vend" > "$d/vendor"
    mkdir -p "$t/sys/class/drm/card$i"; ln -s "$d" "$t/sys/class/drm/card$i/device"
    [ "$kind" = boot ] || [ "$first" = 1 -a "$cards" = "$c" ] && echo 1 > "$d/boot_vga"
    case "$kind" in boot*) echo 1 > "$d/boot_vga";; esac
    i=$((i+1)); first=0
  done
  printf '#!/bin/sh\nprintf "%b"\n' "$lines" | sed 's/^/ /' > /dev/null
  cat > "$t/bin/lspci" <<L
#!/bin/sh
printf '$lines'
L
  cat > "$t/bin/modinfo" <<L
#!/bin/sh
for id in $nvalias; do echo "pci:v000010DEd0000\${id}sv*sd*bc03sc*i*"; done
L
  printf '#!/bin/sh\n[ "%s" = 1 ] && echo "nouveau 1 0"\n' "$nouv" > "$t/bin/lsmod"
  printf '#!/bin/sh\nexit 1\n' > "$t/bin/rmmod"
  printf '#!/bin/sh\n[ "%s" = 1 ]\n' "$mpok" > "$t/bin/modprobe"
  chmod +x "$t"/bin/*
  PATH="$t/bin:$PATH" KESTREL_RUN="$t/run" KESTREL_SYSFS="$t/sys" KESTREL_PERSIST="$t/persist" sh "$SEL"
  got=$(cat "$t/run/kestrel-gpu"); wlr=$(grep -c '^WLR_DRM_DEVICES=' "$t/run/kestrel-gpu.env")
  if [ "$got" = "$exp" ] && [ "$wlr" = "$expwlr" ]; then echo "PASS $name -> $got (WLR_DRM_DEVICES lines=$wlr)"; else echo "FAIL $name: got $got wlr=$wlr expected $exp wlr=$expwlr"; fail=1; fi
  rm -rf "$t"
}
run amd-only        "boot:1002:73bf"                     ""        0 1 mesa 0
run nv-supported    "boot:10de:2684"                     "2684"    0 1 nvidia-open 0
run nv-new-id       "boot:10de:2b85"                     "2B85"    0 1 nvidia-open 0
run nv-unsupported  "boot:10de:1c82"                     "2684"    0 1 nouveau-nvk 0
run nv-modprobe-bad "boot:10de:2684"                     "2684"    0 0 nouveau-nvk 0
run nv-nouveau-busy "boot:10de:2684"                     "2684"    1 1 nouveau-nvk 0
run hybrid-amd-nv   "boot:1002:1681 other:10de:2684"     "2684"    0 1 nvidia-open 1
run amd+nv-desktop  "boot:10de:2684 other:1002:73bf"     "2684"    0 1 nvidia-open 1
exit $fail
