#!/bin/bash
# Version Update Script for Vijenex CIS Scanner
# Usage: ./scripts/update-version.sh v1.0.2

set -euo pipefail

if [ $# -ne 1 ]; then
    echo "Usage: $0 <version>"
    echo "Example: $0 v1.0.2"
    exit 1
fi

NEW_VERSION="$1"

# Validate version format
if [[ ! "$NEW_VERSION" =~ ^v[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    echo "Error: Version must be in format vX.Y.Z (e.g., v1.0.2)"
    exit 1
fi

echo "🔄 Updating version to $NEW_VERSION..."

# Update README.md
echo "📝 Updating README.md..."
sed -i.bak "s|archive/refs/tags/v[0-9]\+\.[0-9]\+\.[0-9]\+\.tar\.gz|archive/refs/tags/$NEW_VERSION.tar.gz|g" README.md
sed -i.bak "s|linux-cis-scanner-[0-9]\+\.[0-9]\+\.[0-9]\+|linux-cis-scanner-${NEW_VERSION#v}|g" README.md
sed -i.bak "s|--branch v[0-9]\+\.[0-9]\+\.[0-9]\+|--branch $NEW_VERSION|g" README.md
sed -i.bak "s|\*\*Current Version\*\*: v[0-9]\+\.[0-9]\+\.[0-9]\+|\*\*Current Version\*\*: $NEW_VERSION|g" README.md
sed -i.bak "s|- \*\*v[0-9]\+\.[0-9]\+\.[0-9]\+\*\*|- \*\*$NEW_VERSION\*\*|g" README.md

# Clean up backup files
rm -f README.md.bak

echo "✅ Version updated to $NEW_VERSION"
echo ""
echo "📋 Next steps:"
echo "1. Review changes: git diff"
echo "2. Commit changes: git add . && git commit -m 'Update version to $NEW_VERSION'"
echo "3. Create tag: git tag -a $NEW_VERSION -m 'Release $NEW_VERSION'"
echo "4. Push: git push origin main && git push origin $NEW_VERSION"