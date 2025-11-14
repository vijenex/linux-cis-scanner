#!/bin/bash

# Update README.md with latest version
# This script updates version references in README.md

set -e

# Get the latest tag
LATEST_TAG=$(git describe --tags --abbrev=0)
echo "Latest tag: $LATEST_TAG"

# Update README.md
sed -i.bak "s/v1\.0\.1/$LATEST_TAG/g" README.md

# Update version references
sed -i.bak "s/linux-cis-scanner-1\.0\.1/linux-cis-scanner-${LATEST_TAG#v}/g" README.md

echo "✅ Updated README.md with version $LATEST_TAG"

# Show changes
echo "📋 Changes made:"
diff README.md.bak README.md || true

# Clean up backup
rm README.md.bak

echo "🎉 README version update completed!"