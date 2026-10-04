# Start the windowed desktop session on tty1 only
if [ -z "${WAYLAND_DISPLAY:-}" ] && [ "$(tty)" = "/dev/tty1" ]; then
  exec /usr/local/bin/kestrel-session
fi
