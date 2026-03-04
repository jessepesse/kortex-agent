#!/usr/bin/env bash
set -euo pipefail

echo "==> Kortex release preflight"

if ! command -v npm >/dev/null 2>&1; then
  echo "ERROR: npm is required for frontend checks."
  exit 1
fi

if ! command -v pytest >/dev/null 2>&1; then
  echo "ERROR: pytest is required for backend checks."
  exit 1
fi

if ! command -v timeout >/dev/null 2>&1; then
  echo "ERROR: timeout command is required."
  exit 1
fi

echo "==> Frontend dependency lock check (npm ci)"
npm --prefix frontend ci

echo "==> Frontend lint"
npm --prefix frontend run lint

echo "==> Frontend build"
npm --prefix frontend run build

echo "==> Backend tests"
timeout 180s pytest --tb=short -q

echo "==> Backend tests (stability re-run)"
timeout 180s pytest --tb=short -q

echo "==> Security scan"
./scripts/security_check.sh

if [[ "${KORTEX_SKIP_DOCKER_SMOKE:-0}" == "1" ]]; then
  echo "==> Docker smoke test skipped (KORTEX_SKIP_DOCKER_SMOKE=1)"
else
  echo "==> Docker smoke test"
  ./scripts/docker_release_smoke.sh
fi

echo "==> Preflight passed"
