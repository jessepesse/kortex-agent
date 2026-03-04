# Security Policy

## Supported Versions

Only the latest version of Kortex Agent is currently supported with security updates.

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |
| < 1.0   | :x:                |

## Reporting a Vulnerability

We take the security of Kortex Agent seriously. If you have discovered a security vulnerability, we appreciate your help in disclosing it to us in a responsible manner.

### Process

1.  **Do not open a public issue.** Security vulnerabilities should be handled discreetly to protect users.
2.  **Email us** (or use the "Private Vulnerability Reporting" feature on GitHub if enabled).
3.  Include as much information as possible:
    *   Type of vulnerability (e.g., XSS, SQL Injection, RCE)
    *   Full paths of source file(s) involved
    *   Step-by-step instructions to reproduce the issue
    *   Proof-of-concept code or screenshots

### Response Timeline

*   We will acknowledge your report within **48 hours**.
*   We will provide a timeline for the fix after assessment.
*   Once fixed, we will release a security patch and credit you (if desired).

## Best Practices

*   Keep Kortex Agent updated to the latest version.
*   Do not share your `.env` file or `config.json` containing API keys.
*   Run Kortex Agent in a secure environment (e.g., behind a firewall, VPN, or on localhost).
*   Kortex is intended for local-only use. Keep backend/frontend bound to localhost.
*   Do not expose Kortex API directly to the public internet.

## Network Exposure Policy

By default, backend binds to `127.0.0.1` (localhost only).

If you override binding (for example `KORTEX_BIND_HOST=0.0.0.0` in Docker), you are responsible for keeping host-level bindings local-only and adding proper perimeter controls. Default `docker-compose.yml` publishes ports only on `127.0.0.1`.

Thank you for helping keep Kortex Agent secure!
