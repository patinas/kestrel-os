# Sourced helper: qemu_launch <serial-log> <timeout-sec> [extra qemu args...]; waits for exit or a CI_FAIL marker.
qemu_base(){
  local cpu=max
  QEMU=(qemu-system-x86_64 -machine "q35,accel=$ACCEL" -cpu "$cpu" -m 4096 -smp 4
    -drive if=pflash,format=raw,readonly=on,file="$(cat "$VM/ovmf-code")"
    -drive if=pflash,format=raw,file="$VM/OVMF_VARS.fd"
    -drive if=none,id=testdisk,format=qcow2,file="$VM/disk.qcow2",discard=unmap,detect-zeroes=unmap
    -device virtio-blk-pci,drive=testdisk,serial=KESTREL_TEST_ONLY
    -virtfs "local,path=$B,mount_tag=kestreltest,security_model=none,readonly=on"
    -device virtio-rng-pci -vga virtio -device virtio-net,netdev=n -netdev user,id=n
    -display none -monitor none)
}
qemu_launch(){
  local log=$1 tmo=$2; shift 2
  qemu_base
  "${QEMU[@]}" -serial "file:$log" "$@" &
  local pid=$! t=0
  while kill -0 "$pid" 2>/dev/null; do
    sleep 10; t=$((t+10))
    if grep -q '^CI_FAIL' "$log" 2>/dev/null; then echo "guest reported failure"; kill "$pid" 2>/dev/null || true; wait "$pid" 2>/dev/null || true; return 3; fi
    if [ "$t" -ge "$tmo" ]; then echo "timeout after ${tmo}s"; kill "$pid" 2>/dev/null || true; wait "$pid" 2>/dev/null || true; return 4; fi
    [ $((t % 300)) -eq 0 ] && echo "[$(date +%T)] qemu running ${t}s, last serial: $(tail -c 200 "$log" 2>/dev/null | tr '\r\n' '  ')"
  done
  wait "$pid" 2>/dev/null || true
  return 0
}
