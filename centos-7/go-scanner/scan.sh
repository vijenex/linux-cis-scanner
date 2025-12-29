#!/bin/bash
# Run Vijenex CIS Scanner for CentOS 7
# Auto-detects architecture and runs the appropriate binary

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Detect architecture
ARCH=$(uname -m)
if [ "$ARCH" = "x86_64" ]; then
    BINARY="bin/vijenex-cis-amd64"
elif [ "$ARCH" = "aarch64" ] || [ "$ARCH" = "arm64" ]; then
    BINARY="bin/vijenex-cis-arm64"
else
    echo "❌ Unsupported architecture: $ARCH"
    echo "Supported: x86_64, aarch64"
    exit 1
fi

# Check if binary exists
if [ ! -f "$BINARY" ]; then
    echo "❌ Binary not found: $BINARY"
    echo ""
    echo "Building scanner..."
    if [ ! -f "build.sh" ]; then
        echo "❌ build.sh not found. Please ensure you're in the go-scanner directory"
        exit 1
    fi
    ./build.sh
fi

# Make executable
chmod +x "$BINARY"

# Default output directory
OUTPUT_DIR="${1:-./reports}"

# Run scanner
echo "🔍 Running Vijenex CIS Scanner for CentOS 7..."
echo "📋 Architecture: $ARCH"
echo "📁 Output: $OUTPUT_DIR"
echo ""

# Run with sudo if not root (for some checks that need root)
if [ "$EUID" -ne 0 ]; then
    echo "⚠️  Warning: Not running as root. Some checks may fail."
    echo "   For complete scan, run: sudo ./scan.sh"
    echo ""
    exec "$BINARY" --output-dir "$OUTPUT_DIR" "${@:2}"
else
    exec "$BINARY" --output-dir "$OUTPUT_DIR" "${@:2}"
fi

