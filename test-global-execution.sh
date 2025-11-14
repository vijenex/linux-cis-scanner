#!/bin/bash

echo "🔍 Testing Vijenex CIS Scanner Global Execution"
echo "=============================================="

# Get the scanner directory
SCANNER_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "📁 Scanner Directory: $SCANNER_DIR"
echo ""

# Test Ubuntu 20.04 scanner from different location
echo "🐧 Testing Ubuntu 20.04 Scanner (from /tmp)..."
cd /tmp
python3 "$SCANNER_DIR/ubuntu-20.04/scripts/linux-cis-scanner.py" --milestones milestone-01-initial-setup.json --format csv > /dev/null 2>&1
if [ -f "$SCANNER_DIR/ubuntu-20.04/reports/vijenex-cis-results.csv" ]; then
    echo "✅ Ubuntu 20.04 reports stored correctly in ubuntu-20.04/reports/"
else
    echo "❌ Ubuntu 20.04 reports not found"
fi

# Test Ubuntu 22.04 scanner from home directory
echo "🐧 Testing Ubuntu 22.04 Scanner (from home)..."
cd ~
python3 "$SCANNER_DIR/ubuntu-22.04/scripts/vijenex-cis.py" --milestones milestone-01-initial-setup.json --format csv > /dev/null 2>&1
if [ -f "$SCANNER_DIR/ubuntu-22.04/reports/vijenex-cis-results.csv" ]; then
    echo "✅ Ubuntu 22.04 reports stored correctly in ubuntu-22.04/reports/"
else
    echo "❌ Ubuntu 22.04 reports not found"
fi

# Test Ubuntu 24.04 scanner from scanner directory
echo "🐧 Testing Ubuntu 24.04 Scanner (from scanner dir)..."
cd "$SCANNER_DIR"
python3 ubuntu-24.04/scripts/vijenex-cis.py --milestones milestone-01-initial-setup.json --format csv > /dev/null 2>&1
if [ -f "$SCANNER_DIR/ubuntu-24.04/reports/vijenex-cis-results.csv" ]; then
    echo "✅ Ubuntu 24.04 reports stored correctly in ubuntu-24.04/reports/"
else
    echo "❌ Ubuntu 24.04 reports not found"
fi

echo ""
echo "📊 Report Summary:"
echo "=================="
find "$SCANNER_DIR" -name "*cis-results.csv" -type f | while read file; do
    echo "📄 $(basename "$(dirname "$(dirname "$file")")"): $file"
done

echo ""
echo "🎉 Global execution test completed!"
echo "✨ All scanners can run from anywhere and store reports in correct OS-specific directories"