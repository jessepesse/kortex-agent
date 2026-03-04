#!/usr/bin/env bash
set -euo pipefail

echo "==> Docker release smoke test"

if ! command -v docker >/dev/null 2>&1; then
  echo "ERROR: docker is required for release smoke test."
  exit 1
fi

if ! docker compose version >/dev/null 2>&1; then
  echo "ERROR: docker compose is required for release smoke test."
  exit 1
fi

cleanup() {
  docker compose down -v >/dev/null 2>&1 || true
}
trap cleanup EXIT

echo "==> Starting stack"
docker compose up -d --build

echo "==> Waiting for backend health"
for i in $(seq 1 60); do
  if curl -fsS http://localhost:5001/api/health >/dev/null 2>&1; then
    echo "Backend health endpoint is ready."
    break
  fi
  if [ "$i" -eq 60 ]; then
    echo "ERROR: backend health endpoint did not become ready in time."
    docker compose logs
    exit 1
  fi
  sleep 2
done

echo "==> Validating local-only port bindings"
backend_binding="$(docker compose port backend 5001 | tr -d '\r')"
frontend_binding="$(docker compose port frontend 3000 | tr -d '\r')"
echo "backend:  ${backend_binding}"
echo "frontend: ${frontend_binding}"

if [[ "${backend_binding}" != 127.0.0.1:* ]]; then
  echo "ERROR: backend is not bound to localhost-only host port."
  exit 1
fi

if [[ "${frontend_binding}" != 127.0.0.1:* ]]; then
  echo "ERROR: frontend is not bound to localhost-only host port."
  exit 1
fi

echo "==> Docker smoke test passed"
