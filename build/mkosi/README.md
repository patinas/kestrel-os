# x86 VM prototype

This is a first build recipe, not an installable release or a tested image.
It targets UEFI x86_64 with Arch Linux, Chromium and Cage (a temporary kiosk
compositor). The own Kestrel shell and secure A/B image are not built yet.

On a host with current mkosi, pacman, systemd-nspawn, QEMU and OVMF installed:

```sh
cd build/mkosi
mkosi summary
mkosi build
mkosi qemu
```

Do not expose this image to untrusted networks or use it as a daily OS. A
successful build is not a successful boot. Before declaring the first-boot
milestone, verify the image reaches Chromium in the VM and record the host,
package versions, boot log and screenshot. The session launch unit and a
non-root user are still TODO, so the current recipe cannot reach the intended
browser session automatically.

This recipe deliberately does not include passwords or auto-login. Do not
solve that by committing a static password. Add a secure first-boot user setup
and a non-root graphical session in the next iteration.
