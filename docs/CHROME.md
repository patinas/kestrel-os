# Chrome download route (not yet CI tested)

The shell requires Google Chrome, downloaded by the end user after explicit local terms acceptance. Chrome binaries are not in the ISO or repository. No Chromium fallback is launched. Neither Chromium nor Chrome binaries are bundled. A fresh non-persistent live boot needs network and acceptance again.

The setup downloads Google's RPM and signing key over verified HTTPS, checks Google's published primary fingerprint and package signature, extracts into writable user storage, and uses Chrome's normal user-namespace sandbox (no --no-sandbox flag). Arch compatibility and dependency coverage are pending CI.

Terms: https://www.google.com/chrome/terms/ and https://policies.google.com/terms (personal, nonassignable software license; no public redistribution grant found). Official Linux platforms/packages: https://support.google.com/chrome/a/answer/9025926?hl=en. Key fingerprint and verification guidance: https://www.google.com/linuxrepositories/.

For installed writable-home systems, run `kestrel-chrome-setup --update` to fetch and verify a fresh package, then restart the session. Automatic security updates are not implemented; this is an alpha limitation. Fresh live boots fetch the current stable package.

Release remains draft until Chrome and interaction tests pass. Earlier Chromium test results do not establish Chrome results. A/B health now checks Chrome processes and needs retesting.
