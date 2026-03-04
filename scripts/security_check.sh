#!/usr/bin/env bash
set -euo pipefail
# Run Bandit security check
# Excludes venv, tests, and other non-production directories

echo "🔍 Running Bandit Security Scan..."
echo "================================="

# Activate venv if exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Run bandit
# -r: recursive
# -ll: report only medium and high severity
# -x: exclude paths
bandit -r . \
    -x ./venv,./tests,./.git,./__pycache__,./data.example \
    -ll

echo "================================="
echo "✅ Scan Complete"
