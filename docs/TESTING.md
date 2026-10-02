# VM test record

Tests completed October 2-3, 2026. These are local QEMU results, not hardware certification.

## Live ISO

UEFI QEMU/KVM boot reached the Chromium/Cage browser shell. The 1280x800 screen showed the search box and Mail, Video and Games buttons. Browser interaction, external navigation and games were not tested.

M1 artifact:
- Size: 1,832,355,840 bytes.
- SHA256: `f40944182f8fa6416f08a383bf4b275da169c667388c4027f77f1974b063e146`.

M2 test artifact:
- Filename: `kestrel-os-2026.10.02-x86_64.iso`.
- Size: 2,747,293,696 bytes.
- SHA256: `90277d9e942b32e3f73d4c618da2e5b7759da9a7cce486122219fa39974034e8`.

These artifacts have not been uploaded as a downloadable release. Arch package versions and the container base are rolling inputs, so a later rebuild is not expected to produce the same hash.

## Installer and installed boot

The opt-in test service ran inside the live VM, targeting only a disposable 24 GiB qcow2 attached as a virtio disk with serial `KESTREL_TEST_ONLY`. Package signatures remained enabled. After fixing mirror and keyring setup, the guest logged:

```
Installed to /dev/vda. Slots A and B populated; default A.
```

The installation VM was stopped. A new QEMU launch supplied only the qcow2 and UEFI firmware, with no ISO, external kernel or initramfs. Its firmware menu selected Kestrel OS (A). After 150 seconds the screenshot showed the browser shell. The screenshot was inspected visually. The VM was then stopped.

Both slots were populated, but only default slot A boot was tested. This test does not prove an update or rollback.

## Reproduction and limits

`build/scripts/install-test-container.sh` is a destructive guest test harness. It preserves an existing test disk if one exists; do not rerun it expecting an empty disk. Review its paths and guards before use. The opt-in installer runs only with the `kestrel.install-test` guest kernel argument.

`build/scripts/disk-boot-container.sh` runs the disk-only boot harness. It writes `build/out/boot.png` and a serial log, then stops the guest. Keep a copy of prior evidence before rerunning.

The test containers use one CPU, a 3 GiB RAM limit, low CPU/I/O priority and disk-backed work. QEMU gets 2 GiB RAM. Only `/dev/kvm` is passed into these test containers; host block devices are not exposed. No host packages were installed for these tests.

## Known gaps

- `kestrel-health.target` and health-gated `systemd-bless-boot` wiring are absent. Automatic rollback is not verified.
- No update signing key or release distribution pipeline has been established.
- The installer does not copy `usr/local/lib/kestrel` or install the full gaming package set. The installed updater and gaming path therefore remain incomplete.
- The NVIDIA device-ID heuristic is unverified and is not a compatibility guarantee.
- The shell footer incorrectly labels the installed system as a live image.
- No ARM build, real hardware, GPU acceleration, gaming, suspend, audio, Wi-Fi or network interaction test is recorded.
