---
category: security
audience: users, operators
area: security
action: Use the private setup-token file for first-run setup; automatic updates now require signed release bundles. FreeBSD needs a native GitHub CLI with attestation support.
breaking: true
---
First-run administration, API credentials, downloads, backups and updates are hardened. Automatic updates now verify signed release attestations, and browser-assisted downloads require an isolated Linux sandbox. Existing external authentication and encrypted backups remain supported. Regenerate calendar links to use restricted feed credentials.
