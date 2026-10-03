# GitHub Actions VM test (manual)

`.github/workflows/vm-test.yml` (workflow_dispatch only; public ubuntu runner; no secrets; nothing uploaded, evidence is the job log and step summary).

Steps (scripts in this directory): 00 host (free disk, work dir on the roomier of / and /mnt, `/dev/kvm` accessible only to the runner group, else TCG), 01 build the live ISO in an Arch container, 02 test minisign key + live kernel + 40 GiB thin qcow2 + persistent OVMF vars, 03 install from the live ISO guest using the repo's current overlay over read-only 9p (`jobs/ci-install.sh`), 04 boot loop driving `jobs/ci.sh`.

`jobs/ci.sh` stages (state on the data partition):
0. boot A (armed +3): health gate + bless; corrupted signature must fail with "signature verification FAILED" and leave entries and rootB untouched; signed update A->B; A stays known good.
1. boot B: health + bless; signed update B->A.
2. boot A: health + bless; signed update A->B armed with `kestrel.test_crash_shell=1`.
3. boot B three times: health gate fails, entry stays unblessed, guest reboots; fourth boot must be A (known good), B entry exhausted (`+0`).

Success marker `CI_DONE_OK`; any `CI_FAIL` stops the run. Test keys are generated per run and never leave the runner. TCG is several times slower; the job limit is 350 minutes and may not suffice without KVM.
