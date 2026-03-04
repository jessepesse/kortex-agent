# Release Checklist

Use this checklist before creating any tag/release.

## Pre-Tag Gates

- [ ] Worktree clean (except intentional files)
- [ ] `./scripts/preflight_release.sh` passes
- [ ] Changelog updated for target version
- [ ] Version synced (`frontend/package.json`, `setup.py`, `kortex/__init__.py`, `README.md`, `kortex/backup.py`)
- [ ] Release notes drafted (summary + full changelog)

## Tag & Push

- [ ] Create release commit
- [ ] Create tag (`vX.Y.Z` or `vX.Y.Z-betaN`)
- [ ] Push `main` and tags
- [ ] Confirm CI `Run Tests` workflow starts

## GitHub Release

- [ ] Verify release exists (auto-created or manual)
- [ ] Set title and publish final notes with `gh release edit/create`
- [ ] Confirm prerelease flag for alpha/beta/rc tags
- [ ] Open release URL and verify rendered notes

## Post-Release Validation

- [ ] Verify Docker images/build jobs complete (if applicable)
- [ ] Smoke-test core endpoints (`/api/health`, chat, council)
- [ ] Announce release with changelog highlights
