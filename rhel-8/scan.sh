#!/bin/bash
# Simple scanner launcher - auto-detects and runs

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Check Python
if command -v python3 &> /dev/null && [ -f "$SCRIPT_DIR/scripts/vijenex-cis.py" ]; then
    echo "Using Python Scanner..."
    cd "$SCRIPT_DIR"
    exec python3 scripts/vijenex-cis.py "$@"
fi

# Check Go binary - detect architecture
ARCH=$(uname -m)
if [ "$ARCH" = "x86_64" ]; then
    GO_BINARY="$SCRIPT_DIR/vijenex-cis-amd64"
elif [ "$ARCH" = "aarch64" ] || [ "$ARCH" = "arm64" ]; then
    GO_BINARY="$SCRIPT_DIR/vijenex-cis-arm64"
else
    GO_BINARY="$SCRIPT_DIR/vijenex-cis-binary"
fi

if [ -f "$GO_BINARY" ]; then
    echo "Using Go Binary ($ARCH)..."
    cd "$SCRIPT_DIR"
    exec "$GO_BINARY" "$@"
fi

echo "ERROR: No scanner available"
echo "Install Python: sudo yum install python3"
exit 1
