#!/bin/bash
# Simple scanner launcher - auto-detects and runs

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Check Python
if command -v python3 &> /dev/null && [ -f "$SCRIPT_DIR/scripts/vijenex-cis.py" ]; then
    echo "Using Python Scanner..."
    cd "$SCRIPT_DIR"
    exec python3 scripts/vijenex-cis.py "$@"
fi

# Check Go binary
if [ -f "$SCRIPT_DIR/vijenex-cis-binary" ]; then
    echo "Using Go Binary..."
    cd "$SCRIPT_DIR"
    exec ./vijenex-cis-binary "$@"
fi

if [ -f "$SCRIPT_DIR/go-scanner/bin/vijenex-cis" ]; then
    echo "Using Go Binary..."
    cd "$SCRIPT_DIR/go-scanner"
    exec ./bin/vijenex-cis "$@"
fi

echo "ERROR: No scanner available"
echo "Install Python: sudo yum install python3"
exit 1
