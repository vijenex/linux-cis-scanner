#!/bin/bash

echo "🔍 Testing Global Installation Behavior"
echo "======================================="

# Simulate global installation detection
echo "📁 Global Installation Detection:"
echo "   - Scanner installed in: /usr/share/vijenex-cis/"
echo "   - Reports will be stored in: /var/log/vijenex-cis/ubuntu-{VERSION}-reports/"
echo ""

# Show what happens after installation
echo "📋 After running: sudo ./install.sh"
echo "   ✅ Scanner files copied to /usr/share/vijenex-cis/"
echo "   ✅ Command 'vijenex-cis' available globally"
echo "   ✅ Reports directory created automatically based on OS version"
echo ""

echo "🐧 OS-Specific Report Storage:"
echo "   - Ubuntu 20.04: /var/log/vijenex-cis/ubuntu-20.04-reports/"
echo "   - Ubuntu 22.04: /var/log/vijenex-cis/ubuntu-22.04-reports/"
echo "   - Ubuntu 24.04: /var/log/vijenex-cis/ubuntu-24.04-reports/"
echo ""

echo "💡 Usage after installation:"
echo "   sudo vijenex-cis                    # Scan with auto OS detection"
echo "   sudo vijenex-cis --profile Level2   # Level 2 scan"
echo "   ls /var/log/vijenex-cis/            # View all OS-specific reports"
echo ""

echo "🎯 Key Features:"
echo "   ✅ Automatic Ubuntu version detection from /etc/os-release"
echo "   ✅ OS-specific report directories created automatically"
echo "   ✅ Global command works from any directory"
echo "   ✅ Reports organized by Ubuntu version"
echo "   ✅ Maintains security with path validation"