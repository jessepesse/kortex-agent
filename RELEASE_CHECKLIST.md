# Release Checklist

Use this checklist before creating any version tag (`vX.Y.Z` or `vX.Y.Z-betaN`).

## 0) Repository State

- [ ] Branch is `main`
- [ ] Worktree is clean (no unintended local changes)
- [ ] Latest commits are pushed and synced with `origin/main`

## 1) Required Quality Gates (Local)

- [ ] Run preflight: `./scripts/preflight_release.sh`
- [ ] Preflight includes:
- [ ] `npm --prefix frontend ci`
- [ ] `npm --prefix frontend run lint`
- [ ] `npm --prefix frontend run build`
- [ ] `pytest` with timeout + stability re-run
- [ ] `./scripts/security_check.sh` (Bandit)
- [ ] `./scripts/docker_release_smoke.sh` (health + localhost bindings)
- [ ] If Docker is intentionally unavailable: set `KORTEX_SKIP_DOCKER_SMOKE=1` and record reason in release notes

## 2) Required Quality Gates (GitHub/CI)

- [ ] `Run Tests` workflow is green on latest commit
- [ ] Branch protection for `main` requires `Run Tests` before merge
- [ ] No failing required checks on the release commit

## 3) Versioning and Notes

- [ ] Version synchronized in:
- [ ] `frontend/package.json`
- [ ] `setup.py`
- [ ] `kortex/__init__.py`
- [ ] `README.md`
- [ ] `kortex/backup.py`
- [ ] `CHANGELOG.md` updated for target version
- [ ] Release notes drafted (highlights + full changelog)
- [ ] For alpha/beta/rc tag, release is marked prerelease

## 4) Security/Deployment Defaults

- [ ] Local-first defaults preserved (`127.0.0.1` host bindings)
- [ ] Non-local deployment docs include auth requirements (`KORTEX_REQUIRE_AUTH`, `KORTEX_API_TOKEN`)
- [ ] Baseline non-local threat model documented in `SECURITY.md`

## 5) Tag, Push, Release

- [ ] Create release commit
- [ ] Create tag (`git tag -a vX.Y.Z -m "Release vX.Y.Z"`)
- [ ] Push branch + tag(s)
- [ ] Verify release entry on GitHub (auto-created or `gh release create`)

## 6) Post-Release Verification

- [ ] Confirm CI for the tag is green (tests + Docker jobs)
- [ ] Verify release notes rendering and links
- [ ] Smoke-check `/api/health` from built artifact/runtime
