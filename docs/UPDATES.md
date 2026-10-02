# Update server and health-check design
Status: proposed design, not implemented or verified. M1 is an x86_64 live ISO only.


Free and static: updates are files on GitHub Releases (or any static host). No server code to run.

## Artifacts per release
- `root-<ver>-<arch>.tar.zst` (full root tree) or later a delta
- `manifest.json`: {version, arch, sha256, size, min_version, channel, url}
- `manifest.json.sig`: detached minisign signature; the public key is baked into the image at /etc/kestrel/update.pub. Updates with a bad signature are rejected.
Channels: stable, beta (separate manifest paths: /stable/manifest.json).

## Client (kestrel-updater, systemd timer every 6h + at boot after network)
1. Fetch manifest, verify signature, compare version, check min_version.
2. Download to the data partition, verify sha256.
3. Write to the inactive slot (see scripts/update.sh), install loader entry, `bootctl set-oneshot` to the new slot.
4. Reboot at idle (or on user prompt); never during gaming mode.

## Health check and rollback
- Boot counting via systemd-boot "boot assessment": entry `kestrel-b+3.conf` (3 tries). `systemd-bless-boot.service` marks good only when `kestrel-health.target` is reached.
- kestrel-health.target requires: network-online (soft), kestrel-session running 60s without crash, `kestrel-health-check` script passes (shell page loads via headless curl of the local file, display server up, root mounted ro).
- If the target is not reached in 3 boots, systemd-boot falls back to the previous slot automatically. The updater marks that version as bad and does not retry it until a newer one appears.
- User data (/var, home) stays on the separate data partition; "powerwash" = reformat data partition from the boot menu.

## Security notes
Read-only roots (dm-verity as a later step), signed manifests, HTTPS only, no telemetry. Key rotation: ship the next public key in the previous release.
