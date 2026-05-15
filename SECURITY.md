# Pulsarr Security Policy

Thank you for taking responsibility and reporting potential security issues in Pulsarr.

At present this repository does not accept private vulnerability reports via a configured private channel. Please follow the instructions below.

1) Public reporting (preferred / default)

- Open a new GitHub Issue in this repository and use the prefix `SECURITY:` in the title, for example:

```
SECURITY: SQL injection in parsing module
```

- In the issue body include: affected component, reproducible steps, versions, PoC (if available), and your contact information.

- Set the issue labels to `security` (maintainers will triage).

2) Private reporting (optional - not currently configured)

- If you require a private disclosure channel, reach out to the repository maintainers directly. Add an email contact in this file or create a private disclosure process and update this document. Example placeholder (update before public use): `security@your-organization.example`.

3) Response expectations

- Maintainers aim to acknowledge reports within 72 hours and will publish remediation guidance or advisories via GitHub Security Advisories when appropriate.

4) Sensitive data

- Do not paste secrets or full private keys into public issues. If you accidentally committed a secret, enable secret rotation immediately and notify maintainers.

5) If you are a security researcher

- If you would like credit, indicate in your report whether you'd like to be listed in the `SECURITY.md` or an advisory as the reporter.

---

Maintainers: please replace the placeholder contact email above with an actual private disclosure address if you want to enable private reporting.
