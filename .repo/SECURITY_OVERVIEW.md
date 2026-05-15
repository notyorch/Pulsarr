# Security Overview

This document summarizes the current security configuration and guidance for the Pulsarr repository.

- **Security policy:** Disabled
- **Security advisories:** Enabled
- **Private vulnerability reporting:** Disabled
- **Dependabot alerts:** Disabled
- **Code scanning alerts:** Needs setup
- **Secret scanning alerts:** Enabled

For more details about how to report a vulnerability, see `.repo/SECURITY.md`.

---

Short explanation of each item

- Security policy: A repository-level SECURITY.md file or GitHub security policy is currently not enabled. Adding a `SECURITY.md` to the repository (this folder) provides clear public guidance for reporting issues.

- Security advisories: GitHub's security advisories feature is enabled for maintainers to publish advisories.

- Private vulnerability reporting: Private reporting via GitHub is not enabled; reports should be made publicly per the guidance below unless a private channel is explicitly configured.

- Dependabot alerts: Dependabot alerts are currently disabled. Enable Dependabot if you want automated dependency vulnerability scanning and pull request remediation.

- Code scanning alerts: Not configured. We recommend setting up GitHub Code Scanning (CodeQL) or a third-party scanner to detect common vulnerabilities.

- Secret scanning alerts: Enabled — GitHub will notify repository administrators if suspected secrets are pushed.
