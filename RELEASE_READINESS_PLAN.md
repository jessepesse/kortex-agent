# Release Readiness Roadmap

Last updated: 2026-03-04  
Scope: Track readiness from alpha -> beta -> stable `1.0.0`.

## Current Status

| Milestone | Status | Notes |
| --- | --- | --- |
| `v1.0.0-beta1` | Done | Tag and pre-release published |
| Stable `1.0.0` | In progress | Core hardening items still open |

## Beta Gate Checklist (`v1.0.0-beta1`)

- [x] Deterministic test suite (no hanging network-style tests)
- [x] Timeout protection in CI test runs
- [x] Settings/Backup API contract alignment
- [x] Frontend lint/build enforced in CI
- [x] Version metadata synchronized across repo
- [x] Local-first security defaults documented and implemented

## Stable `1.0.0` Gate Checklist

## 1) API Contract Standardization

- [ ] Standardize response envelope across all routes (`{ success, data, message? }` or documented exceptions)
- [ ] Remove mixed raw JSON response patterns where possible
- [ ] Add route-level schema tests for critical endpoints

Definition of done:
- [ ] API docs and tests reflect one consistent contract

## 2) Reliability and Observability

- [ ] Replace high-noise `print(...)` logging in backend/AI modules with `logging`
- [ ] Keep user-facing errors sanitized while preserving debug detail in logs
- [ ] Validate background task failure visibility (clear logs + non-fatal behavior)

Definition of done:
- [ ] Incidents can be triaged from logs without ad-hoc repro
- [ ] Error handling behavior is consistent across routes/services

## 3) Release Process Hardening

- [ ] Confirm CI quality gates required before merge (`Run Tests`)
- [ ] Ensure release checks include backend tests + frontend lint/build + security scan
- [ ] Validate Docker healthchecks and startup assumptions against current defaults
- [ ] Add explicit release checklist doc for tag/release procedure

Definition of done:
- [ ] Tagging a release always yields tested, reproducible artifacts and clear notes

## Optional Track Before `1.0.0`

Local-first model is already implemented. If future deployment scope expands beyond localhost:
- [x] Add explicit auth for sensitive endpoints (`/api/config/api-keys`, `/api/backup/*`, write routes)
- [x] Add baseline threat model section for non-local deployments (`SECURITY.md`)

## Suggested Sequence

1. API contract cleanup + tests  
2. Logging/observability cleanup  
3. Release process hardening  
4. Final `1.0.0-rc1` (optional) -> `1.0.0`
