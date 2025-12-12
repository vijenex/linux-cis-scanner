#!/bin/bash
# Quick test script for RHEL 8 production server

echo "=========================================="
echo "  RHEL 8 CIS Scanner - Production Test"
echo "=========================================="
echo

# Check if running on RHEL 8
if [ -f /etc/redhat-release ]; then
    echo "✓ Detected: $(cat /etc/redhat-release)"
else
    echo "✗ Not a RHEL system"
    exit 1
fi

# Check Python 3
if command -v python3 >/dev/null 2>&1; then
    echo "✓ Python: $(python3 --version)"
else
    echo "✗ Python 3 not found. Install with: sudo yum install python3"
    exit 1
fi

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "⚠ Warning: Not running as root. Some checks may fail."
    echo "  For complete results, run: sudo ./TEST_ON_PRODUCTION.sh"
    echo
fi

# Create output directory
OUTPUT_DIR="/tmp/vijenex-scan-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$OUTPUT_DIR"

echo
echo "=========================================="
echo "  Starting CIS Scan..."
echo "=========================================="
echo "Output directory: $OUTPUT_DIR"
echo

# Run scanner
python3 scripts/vijenex-cis.py --output-dir "$OUTPUT_DIR" --profile Level1 --format both

echo
echo "=========================================="
echo "  Scan Complete!"
echo "=========================================="
echo "Reports saved to: $OUTPUT_DIR"
echo
echo "View reports:"
echo "  CSV: cat $OUTPUT_DIR/vijenex-cis-results.csv"
echo "  HTML: firefox $OUTPUT_DIR/vijenex-cis-report.html"
echo
echo "Copy reports to your machine:"
echo "  scp -r $(hostname):$OUTPUT_DIR/ ./"
echo "=========================================="
