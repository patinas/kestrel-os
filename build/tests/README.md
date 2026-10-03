# Disposable VM development tests

These scripts are test infrastructure, not a production installer or unattended workflow. They were used only on a disposable 40 GiB qcow2 with exact serial KESTREL_TEST_ONLY. The live rescue/installer launcher can mutate that guest disk. Review each job before use. Existing disks are preserved, not reset automatically.

No more VM load is permitted on the shared TV host after two playback timeouts. A separate suitable test host is needed before these remaining tests can run.

The test overlay is separate from the normal OS profile. It runs jobs only with a guest kernel argument, verified QEMU/KVM identity and exact disk serial. A read-only 9p share supplies jobs; no root SSH or host block device is exposed. Persistent OVMF variables preserve boot assessment across guest restarts.

The host guard probes playback at one-minute start-to-start intervals and stops only the test guest/container on the first failed probe. It never restarts production services. A guard startup path error was caught and corrected before the morning guarded tests; this guard did stop the test on the second TV timeout.

jobs/diagnostics.sh should remain the read-only baseline. jobs/update.sh and jobs/rollback.sh write only the verified guest's inactive slot. Their final revisions are untested. Bad-signature tests must verify the actual signature-failure message, not merely any nonzero exit. Test keys remain under ignored out/test-keys and must never be used for releases or committed.

See ../../docs/TESTING.md for observed results and failures. A black screen, source review or successful image write is not a successful boot or rollback.
