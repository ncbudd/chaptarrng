---
category: security
audience: users, operators
area: authentication, downloads, backups, updates, packaging
action: Use the private setup-token file for first-run setup; automatic updates now require signed release bundles. FreeBSD needs a native GitHub CLI with attestation support.
breaking: true
---
Harden first-run administration, restricted API authorization, browser-session credentials, cover serving, public downloads, archive extraction, database/settings restores and media-tool resource limits. Update installation now requires a signed release-workflow attestation in addition to its checksum. Browser-assisted downloads require an isolated non-root Linux sandbox and fail closed elsewhere. Dependencies and scanner inputs are pinned, development dependencies are scanned, and each PR revision receives a blocking security result. Existing external authentication and legacy encrypted backups remain supported. Live updates reconnect with refreshed browser credentials; newly generated calendar subscriptions use a stable read-only feed credential instead of exposing the master API key. Regenerate existing calendar links to adopt the restricted credential.

See `docs/security/audit-remediation-2026-11-09.md` for all 27 audit dispositions, configuration changes and validation boundaries. GitHub branch protection is a separate administrative action and is not applied by this commit.
