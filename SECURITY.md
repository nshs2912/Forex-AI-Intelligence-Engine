# Security Policy

## Scope

This repository contains a research and decision-support engine for foreign-exchange analytics. It is not an autonomous trading executor, and model artifacts are not approved for live use by code or CI.

## Reporting a vulnerability

Please do not disclose security vulnerabilities in public issues.

Report suspected vulnerabilities privately to the repository maintainers with:
- affected component or file
- reproducible steps
- expected and observed behavior
- potential security impact
- relevant logs or proof of concept, with secrets and personal data removed

Do not include API keys, passwords, broker credentials, or other secrets in reports.

## Security principles

1. Secrets must be supplied through environment variables or GitHub Actions secrets, never committed to source.
2. CI uses least-privilege repository permissions where practical.
3. Model training must never change a model to `approved_for_live`.
4. Live approval requires documented validation evidence and human authorization.
5. Market-data and model provenance should remain auditable.
6. Dependencies should be monitored for known security vulnerabilities.
7. Security fixes should preserve the DSS governance boundary.

## Supported security posture

The default branch is maintained through the normal CI checks before release.

## Out of scope

This policy does not authorize real-money trading, broker access, credential sharing, or bypassing DSS governance controls.
