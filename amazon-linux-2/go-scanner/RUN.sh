#!/bin/bash
# Run Vijenex CIS Scanner for Amazon Linux 2
# Uses pre-built binary - no Go installation required

set -e

# Detect architecture
ARCH=$(uname -m)
if [ "$ARCH" = "x86_64" ]; then
    BINARY="bin/vijenex-cis-linux-amd64"
elif [ "$ARCH" = "aarch64" ]; then
    BINARY="bin/vijenex-cis-linux-arm64"
else
    echo "❌ Unsupported architecture: $ARCH"
    exit 1
fi

# Check if binary exists
if [ ! -f "$BINARY" ]; then
    echo "❌ Binary not found: $BINARY"
    echo "Please clone the full repository with binaries"
    exit 1
fi

# Make executable
chmod +x "$BINARY"

# Run scanner
echo "🔍 Running Vijenex CIS Scanner for Amazon Linux 2..."
echo "📋 Architecture: $ARCH"
echo "🔧 Binary: $BINARY"
echo ""

exec "$BINARY" "$@"
