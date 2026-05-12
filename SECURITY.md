# Security Policy

## Reporting Vulnerabilities

Please do not open a public issue for a security vulnerability.

Email the maintainer or use GitHub private vulnerability reporting when available for
this repository. Include:

- A description of the issue.
- Steps to reproduce.
- Potential impact.
- Any suggested mitigation.

## Scope

`vectormeta` processes local JSON, JSONL, YAML config, and sidecar files. It should not
execute record content. Please report path traversal, overwrite protection bypasses,
unsafe file handling, dependency vulnerabilities, or CLI behavior that could lead to
data loss.
