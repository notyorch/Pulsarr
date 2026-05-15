# Dependency & Scanning Status

This file documents the current status of dependency vulnerability scanning and code scanning for Pulsarr, and provides quick next steps to enable automated protection.

## Status summary

- Dependabot alerts: Disabled
- Code scanning alerts: Needs setup
- Secret scanning alerts: Enabled

## What this means

- Dependabot alerts disabled: the repository will not automatically receive dependency vulnerability alerts or automatic PR fixes from Dependabot until enabled. To enable: go to the repository Settings -> Security -> Configure Dependabot.

- Code scanning needs setup: no automated static analysis is currently configured. We recommend enabling CodeQL (GitHub Code Scanning) or integrating a CI step with a static analyzer. See: https://docs.github.com/en/code-security/secure-your-code

- Secret scanning enabled: GitHub will detect and notify administrators for likely secrets committed to the repository. Ensure any detected secrets are rotated immediately.

## Recommended next steps

1. Enable Dependabot alerts and optionally Dependabot security updates.
2. Configure GitHub Code Scanning (CodeQL) via the Security tab or add a CI workflow for scanning.
3. Review any historical secret scanning findings and rotate secrets if necessary.
