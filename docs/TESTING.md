# VM test record

Tests completed October 2-3, 2026. These are local and public-runner QEMU results, not hardware certification. The CI run 4 section below is the latest end-to-end result.

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

## Known gaps at the earlier M2 test (superseded where noted below)

- `kestrel-health.target` and health-gated `systemd-bless-boot` wiring are absent. Automatic rollback is not verified.
- No update signing key or release distribution pipeline has been established.
- The installer does not copy `usr/local/lib/kestrel` or install the full gaming package set. The installed updater and gaming path therefore remain incomplete.
- The NVIDIA device-ID heuristic is unverified and is not a compatibility guarantee.
- The shell footer incorrectly labels the installed system as a live image.
- No ARM build, real hardware, GPU acceleration, gaming, suspend, audio, Wi-Fi or network interaction test is recorded.

## Revision 3 local test progress (October 3, historical)

The revised full-package installer completed a 552-package transaction on a new 40 GiB disposable QEMU disk with 12 GiB root slots (62% root usage). Installed A boot was read-only, had Steam/gamescope/minisign/nvidia-open and the Kestrel library scripts, and showed the corrected installed footer. In the test harness only, initial A was armed with three boot attempts. The same Cage/Chromium processes survived the 60-second health check; boot-complete.target completed, systemd-bless-boot marked the boot good at attempt 1, and A's counter was removed.

A corrupted detached signature was rejected by the actual signature verifier before boot-entry changes. A valid test-key signed image was written to B, preserving A and arming B+3 version 3. B boot then failed with a black screen and repeated early systemd starts. A live rescue inspection verified that the test image omitted /run and /tmp entirely. Source fixes retain those mountpoint directories in the image and create them defensively during extraction. A later rescue repair proved those missing directories mattered; the corrected extraction path still has no successful end-to-end boot test.

Other source corrections normalize executable modes/ownership (firstboot was copied as 0644 and failed with 203/EXEC), make the updater's lib.sh lookup symlink-safe, and restrict temporary ESP mount permissions. Update packing now streams tar into one zstd worker onto the data partition instead of staging an uncompressed root in RAM.

The first TV degradation occurred at 01:37:04 CEST: HTTP 000/no segments under VM load. Tests stopped; a recheck returned HTTP 200/four segments. The next morning tests resumed under one CPU, nice 19, idle I/O, 2 GiB guest RAM and a 3 GiB container limit with a one-minute playback guard.

At 09:33, the live rescue guest created B's missing /run and /tmp directories, fixed executable modes and copied the symlink-safe updater. B's entry then had one try left after two earlier failed boots. The disk-only B boot reached the shell with rootB read-only; the same Cage/Chromium processes passed the 60-second health check. systemd-bless-boot marked attempt 3 good and removed the counter. The screenshot was inspected visually and showed the installed footer. This proves rescue-repaired B boot and blessing, not the corrected signed-update path.

A subsequent signed B-to-A write using the corrected extractor failed before arming A: permission normalization followed the absolute kestrel-update symlink into the running read-only root. Source-only fixes now use find -type f to avoid following symlinks. These final fixes have syntax checks but no VM proof. The known-good B entry remains; A's entry was retired before the failed write.

The second TV degradation occurred at 09:45:10 CEST despite the lower-priority setup: the one-minute guard got HTTP 000/no segments and stopped the guest/container at that first failed probe. The recheck after stopping returned HTTP 200/four segments. All test guests/container and test wakes are stopped. No further VM load is permitted on this shared TV host. No host disk or host package change was made.

Automatic rollback, three injected unhealthy boots, and a corrected signed-update boot without rescue remain unverified. Test signing keys are local and disposable, not release keys. They are not included in source publication.

## CI harness (manual workflow)

`.github/workflows/vm-test.yml` runs the full install, boot, health/bless, bad-signature, signed A->B->A update and induced-unhealthy rollback sequence on a public runner. See `build/tests/ci/README.md`. Run results are recorded below; run 4 passed.

### Public CI diagnostics, 2026-10-03

Runs 37110324059 and 37111246448 both completed a full install and installed slot A boot on KVM. Their journals show the 60-second health gate passed, then systemd blessed A. Neither run reached a completed bad-signature test or a B boot. Run 2 stopped at a diagnostic `ls` before invoking the verifier. Serial login was active while the job held a serial output descriptor; missing ordinary output suggests a getty reset invalidated that descriptor. The CI-only harness now masks serial-getty on ttyS0 and reopens the serial device for critical diagnostics. This explanation and the adjusted harness require a new CI run; no updater behavior was changed by this fix.

### Public CI run 3, 2026-10-03

https://github.com/patinas/kestrel-os/actions/runs/37114709251 (e46bba6) failed after 44m16s on KVM. It completed real corrupted-signature rejection without slot or entry writes, signed A-to-B update, B health/blessing, signed B-to-A update, A health/blessing, and three induced unhealthy B boots that stayed unblessed. B reached +0-3 and systemd-boot selected the counter-less known-good A. The final assertion failed because fallback A never logged health OK within the test window. Healthy fallback was not proved.

The health service was enabled only through boot-complete.target, which the blessing generator pulls in for counted boots. Counter-less fallback has no such trigger. The revised service is also wanted by multi-user.target on every boot, with ordering before that target to avoid a cycle, and remains active after success. The installer checks both enablement links. This source fix requires another end-to-end CI run; run 3 is not a pass. Failure diagnostics now include service status and guest journals.

### Public CI run 4 passed, 2026-10-03

Run: https://github.com/patinas/kestrel-os/actions/runs/37118001480
Job: https://github.com/patinas/kestrel-os/actions/runs/37118001480/job/111188450230
Tested source: `4ca0a57a5b51ccc6bfdc7873e2369a7988a3728a`. Total duration: 23m42s. KVM was available. No artifacts were uploaded; evidence is in job logs and the job summary.

The run built the live ISO and installed to a disposable 40 GiB qcow2 with 12 GiB root slots. Disk-only boots completed this sequence:

- Installed slot A booted read-only, passed the 60-second same-process Cage/Chromium health gate and was blessed.
- A corrupted detached signature failed the real verifier. Boot-entry hashes and inactive-slot UUID stayed unchanged. The verifier runs before any slot write.
- A test-key signed image updated B while preserving known-good A. B booted, passed health and was blessed.
- A test-key signed image updated A from B. A booted, passed health and was blessed.
- A signed update armed B with three tries and an explicit fault-injection kernel argument. Each B boot killed Chromium during the health hold, failed health and remained unblessed.
- The B entry exhausted its counter. systemd-boot selected known-good A without the crash argument. A logged health OK; the harness logged `CI_STEP fallback_to_known_good_A_after_3_failed_tries`, `CI_DONE_OK`, and stage 4 poweroff. The runner reported success.

The CI health check observes real processes, not mocked Cage/Chromium names. The test overlay extends startup waits, adds a test-job service and disables the serial login. The failure injection is test-only. No guest screenshots were retained in this run, so its result proves the boot/update/health/fallback sequence, not visual UI behavior. Real hardware, GPU/gaming, ARM, browser interaction, production signing keys and release distribution remain unverified. There is still no downloadable release.
