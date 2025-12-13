#!/bin/bash
# Vijenex CIS Scanner - Auto-detects Python or Go and runs

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Check if root
if [ "$EUID" -ne 0 ]; then 
    echo "ERROR: Must run as root"
    echo "Usage: sudo ./scan.sh"
    exit 1
fi

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║           VIJENEX CIS SCANNER - RHEL 8                       ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# Try Python first
if command -v python3 &> /dev/null && [ -f "$SCRIPT_DIR/scripts/vijenex-cis.py" ]; then
    echo "✓ Using Python Scanner"
    echo ""
    cd "$SCRIPT_DIR"
    exec python3 scripts/vijenex-cis.py "$@"
fi

# Fallback to Go binary - detect architecture
ARCH=$(uname -m)
if [ "$ARCH" = "x86_64" ]; then
    GO_BINARY="$SCRIPT_DIR/vijenex-cis-amd64"
elif [ "$ARCH" = "aarch64" ] || [ "$ARCH" = "arm64" ]; then
    GO_BINARY="$SCRIPT_DIR/vijenex-cis-arm64"
else
    GO_BINARY="$SCRIPT_DIR/vijenex-cis"
fi

if [ -f "$GO_BINARY" ]; then
    echo "✓ Using Go Binary ($ARCH)"
    echo ""
    cd "$SCRIPT_DIR"
    exec "$GO_BINARY" "$@"
fi

# No scanner found
echo "❌ ERROR: No scanner available"
echo ""
echo "Install Python: sudo yum install python3"
exit 1
