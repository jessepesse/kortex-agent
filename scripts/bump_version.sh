#!/bin/bash
# Version Bump Script
# Reads version from frontend/package.json and updates all other version references
#
# Usage: ./scripts/bump_version.sh [new_version]
#   If no version provided, syncs from package.json
#   If version provided, updates package.json first then syncs

set -e

cd "$(dirname "$0")/.."

# Get version from package.json or argument
if [ -n "$1" ]; then
    # Update package.json first
    NEW_VERSION="$1"
    sed -i "s/\"version\": \"[^\"]*\"/\"version\": \"$NEW_VERSION\"/" frontend/package.json
    echo "📦 Updated frontend/package.json to $NEW_VERSION"
else
    # Read from package.json
    NEW_VERSION=$(grep '"version"' frontend/package.json | head -1 | sed 's/.*: "\([^"]*\)".*/\1/')
fi

echo "🔄 Syncing version: $NEW_VERSION"

# Update kortex/__init__.py
sed -i "s/__version__ = \"[^\"]*\"/__version__ = \"$NEW_VERSION\"/" kortex/__init__.py
echo "  ✓ kortex/__init__.py"

# Update setup.py
sed -i "s/version=\"[^\"]*\"/version=\"$NEW_VERSION\"/" setup.py
echo "  ✓ setup.py"

# Update kortex/backup.py
sed -i "s/\"kortex_version\": \"[^\"]*\"/\"kortex_version\": \"$NEW_VERSION\"/" kortex/backup.py
echo "  ✓ kortex/backup.py"

# Update README.md
sed -i "s/Version [0-9][^|]*/Version $NEW_VERSION /" README.md
echo "  ✓ README.md"

# Update package-lock.json (only root version)
cd frontend && npm install --package-lock-only 2>/dev/null || true && cd ..
echo "  ✓ frontend/package-lock.json"

echo ""
echo "✅ All versions synced to $NEW_VERSION"
echo ""
echo "Next steps:"
echo "  git add ."
echo "  git commit -m \"Version: Bump to $NEW_VERSION\""
echo "  git tag v$NEW_VERSION"
echo "  git push origin main --tags"
