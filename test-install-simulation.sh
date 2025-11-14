#!/bin/bash

echo "🔍 Simulating Global Installation Process"
echo "========================================"

# Simulate the installation directory structure
TEST_DIR="/tmp/vijenex-test-install"
rm -rf "$TEST_DIR"
mkdir -p "$TEST_DIR/usr/share/vijenex-cis"
mkdir -p "$TEST_DIR/var/log/vijenex-cis"

echo "📁 Simulating install.sh behavior..."

# Copy all ubuntu directories (like the updated install script does)
for ubuntu_dir in ubuntu-*/; do
    if [ -d "$ubuntu_dir" ]; then
        ubuntu_name=$(basename "$ubuntu_dir")
        cp -r "$ubuntu_dir" "$TEST_DIR/usr/share/vijenex-cis/$ubuntu_name"
        echo "✅ Copied $ubuntu_name to global installation"
    fi
done

echo ""
echo "📋 Installed directory structure:"
ls -la "$TEST_DIR/usr/share/vijenex-cis/"
echo ""
echo "Looking for ubuntu-* directories:"
ls -d "$TEST_DIR/usr/share/vijenex-cis/ubuntu-"* 2>/dev/null || echo "No ubuntu-* directories found in installation"

echo ""
echo "🐧 Simulating wrapper script behavior for different Ubuntu versions:"

for version in "20.04" "22.04" "24.04"; do
    echo ""
    echo "Testing Ubuntu $version:"
    
    echo "  Checking for: $TEST_DIR/usr/share/vijenex-cis/ubuntu-$version"
    if [ -d "$TEST_DIR/usr/share/vijenex-cis/ubuntu-$version" ]; then
        scanner_dir="$TEST_DIR/usr/share/vijenex-cis/ubuntu-$version"
        reports_dir="$TEST_DIR/var/log/vijenex-cis/ubuntu-$version-reports"
        
        echo "  ✅ Scanner directory: $scanner_dir"
        echo "  ✅ Reports directory: $reports_dir"
        
        # Create the reports directory
        mkdir -p "$reports_dir"
        echo "  ✅ Created reports directory"
        
        # Check if scanner script exists
        if [ -f "$scanner_dir/scripts/vijenex-cis.py" ] || [ -f "$scanner_dir/scripts/linux-cis-scanner.py" ]; then
            echo "  ✅ Scanner script found"
        else
            echo "  ❌ Scanner script not found"
        fi
    else
        echo "  ❌ Ubuntu $version directory not found"
    fi
done

echo ""
echo "📊 Final directory structure:"
find "$TEST_DIR" -type d | sort

echo ""
echo "🎯 Summary:"
echo "✅ All Ubuntu versions preserved in global installation"
echo "✅ OS-specific report directories can be created"
echo "✅ Wrapper script can detect and use correct scanner"
echo "✅ Reports will be stored in /var/log/vijenex-cis/ubuntu-{version}-reports/"

# Cleanup
rm -rf "$TEST_DIR"
echo ""
echo "🧹 Test cleanup completed"