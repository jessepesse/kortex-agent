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

For non-local deployments, enable API authentication:

- `KORTEX_REQUIRE_AUTH=true`
- `KORTEX_API_TOKEN=<long-random-token>`
- Pass header: `Authorization: Bearer <token>`

When auth is enabled, `/api/*` routes (except `/api/health`) require a valid bearer token.

## Non-Local Threat Model (Baseline)

This section defines the minimum security model for deployments beyond localhost.
Non-local deployment is still advanced usage and requires explicit hardening by operators.

### Assets

- API keys stored in `config.json` / environment variables
- User data in `data/*.json` and `data/conversations/*.json`
- Backup archives from `/api/backup/*`
- Administrative configuration exposed by `/api/config/*`

### Trust Boundaries

- Client (browser/UI) to backend API (`/api/*`)
- Backend process to local filesystem (config, data, backups)
- Optional reverse proxy / container network to backend service
- Host/network perimeter separating trusted private network from internet

### Entry Points

- HTTP API routes on backend (`/api/*`)
- Backup upload/restore endpoints (`/api/backup/validate`, `/api/backup/restore`)
- Configuration write endpoints (`/api/config/api-keys`, `/api/models`, data write routes)

### Security Assumptions

- Local-first defaults remain in place (`127.0.0.1` binds by default)
- Non-local exposure requires `KORTEX_REQUIRE_AUTH=true`
- `KORTEX_API_TOKEN` is high-entropy and kept secret
- TLS termination is handled by a trusted reverse proxy/load balancer
- Network access is restricted (firewall/VPN/private subnet)

### Primary Risks

- Unauthorized API access from weak/missing token controls
- Credential leakage (API keys, bearer token, config files)
- Sensitive data exposure via backup endpoints or misconfigured network binds
- Brute-force and abuse against public endpoints
- Overexposure from `0.0.0.0` binding without perimeter controls

### Required Controls Before Internet Exposure

- Keep host-level port publishing restricted to trusted sources
- Enforce API token auth for all non-health API routes
- Use TLS in transit (HTTPS via reverse proxy)
- Rotate and protect secrets (`KORTEX_API_TOKEN`, provider API keys)
- Monitor logs for auth failures and abnormal request patterns
- Maintain routine dependency/security scanning in CI

Thank you for helping keep Kortex Agent secure!
