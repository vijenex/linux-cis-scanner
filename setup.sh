#!/bin/bash
"""
██╗   ██╗██╗     ██╗███████╗███╗   ██╗███████╗██╗  ██╗
██║   ██║██║     ██║██╔════╝████╗  ██║██╔════╝╚██╗██╔╝
██║   ██║██║     ██║█████╗  ██╔██╗ ██║█████╗   ╚███╔╝ 
╚██╗ ██╔╝██║██   ██║██╔══╝  ██║╚██╗██║██╔══╝   ██╔██╗ 
 ╚████╔╝ ██║╚█████╔╝███████╗██║ ╚████║███████╗██╔╝ ██╗
  ╚═══╝  ╚═╝ ╚════╝ ╚══════╝╚═╝  ╚═══╝╚══════╝╚═╝  ╚═╝

                    Linux CIS Audit Setup
           Powered by Vijenex Security Platform
"""

set -e

echo "Setting up Linux CIS Audit Platform..."
echo "======================================"

# Detect distribution
if [ -f /etc/os-release ]; then
    . /etc/os-release
    DISTRO=$ID
    VERSION=$VERSION_ID
else
    echo "Cannot detect Linux distribution"
    exit 1
fi

echo "Detected: $PRETTY_NAME"

# Check Python 3
if ! command -v python3 &> /dev/null; then
    echo "Python 3 is required but not installed."
    echo "Please install Python 3 first:"
    case $DISTRO in
        ubuntu|debian)
            echo "  sudo apt update && sudo apt install python3"
            ;;
        rhel|centos|fedora)
            echo "  sudo yum install python3"
            ;;
        *)
            echo "  Install Python 3 using your package manager"
            ;;
    esac
    exit 1
fi

echo "Python 3 found: $(python3 --version)"

# Determine appropriate scanner directory
SCANNER_DIR=""
case $DISTRO in
    ubuntu)
        if [[ "$VERSION" == "20.04" ]]; then
            SCANNER_DIR="ubuntu-20.04"
        elif [[ "$VERSION" == "22.04" ]]; then
            SCANNER_DIR="ubuntu-22.04"
        else
            echo "Ubuntu version $VERSION not yet supported"
            echo "Using Ubuntu 20.04 scanner as fallback"
            SCANNER_DIR="ubuntu-20.04"
        fi
        ;;
    debian)
        SCANNER_DIR="debian-11"
        ;;
    rhel)
        if [[ "$VERSION" == "8"* ]]; then
            SCANNER_DIR="rhel-8"
        elif [[ "$VERSION" == "9"* ]]; then
            SCANNER_DIR="rhel-9"
        else
            echo "RHEL version $VERSION not yet supported"
            exit 1
        fi
        ;;
    centos)
        SCANNER_DIR="centos-7"
        ;;
    *)
        echo "Distribution $DISTRO not yet supported"
        echo "Available distributions:"
        ls -d */ | grep -E "(ubuntu|debian|rhel|centos)" | sed 's|/||'
        exit 1
        ;;
esac

if [ ! -d "$SCANNER_DIR" ]; then
    echo "Scanner directory $SCANNER_DIR not found"
    echo "Available directories:"
    ls -d */ | grep -E "(ubuntu|debian|rhel|centos)" | sed 's|/||'
    exit 1
fi

echo "Using scanner: $SCANNER_DIR"

# Make scripts executable
chmod +x $SCANNER_DIR/scripts/*.py

# Create reports directory
mkdir -p $SCANNER_DIR/reports

echo ""
echo "Setup completed successfully!"
echo ""
echo "To run the scanner:"
echo "  cd $SCANNER_DIR"
echo "  sudo python3 scripts/linux-cis-scanner.py"
echo ""
echo "For help:"
echo "  python3 scripts/linux-cis-scanner.py --help"
echo ""
echo "Test basic functionality (no root required):"
echo "  python3 scripts/test-scanner.py"