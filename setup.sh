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

# Error handling function
error_exit() {
    echo "Error: $1" >&2
    exit 1
}

# Exit on any error, undefined variables, or pipe failures
set -euo pipefail

# Error handling function
error_exit() {
    echo "Error: $1" >&2
    exit 1
}

echo "Setting up Linux CIS Audit Platform..."
echo "======================================"

# Detect distribution
if [ -f /etc/os-release ]; then
    # shellcheck source=/etc/os-release
    . /etc/os-release || error_exit "Failed to source /etc/os-release"
    DISTRO="${ID:-unknown}"
    VERSION="${VERSION_ID:-unknown}"
    [ "$DISTRO" = "unknown" ] && error_exit "Could not determine distribution ID"
else
    error_exit "Cannot detect Linux distribution - /etc/os-release not found"
fi

echo "Detected: $PRETTY_NAME"

# Check Python 3
if ! command -v python3 >/dev/null 2>&1; then
    echo "Python 3 is required but not installed."
    echo "Please install Python 3 first:"
    case "$DISTRO" in
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
    error_exit "Python 3 installation required"
fi

echo "Python 3 found: $(python3 --version)"

# Determine appropriate scanner directory
SCANNER_DIR=""
case "$DISTRO" in
    ubuntu)
        if [[ "$VERSION" == "20.04" ]]; then
            SCANNER_DIR="ubuntu-20.04"
        elif [[ "$VERSION" == "22.04" ]]; then
            SCANNER_DIR="ubuntu-22.04"
        elif [[ "$VERSION" == "24.04" ]]; then
            SCANNER_DIR="ubuntu-24.04"
        else
            echo "Ubuntu version $VERSION not yet supported"
            echo "Using Ubuntu 24.04 scanner as fallback"
            SCANNER_DIR="ubuntu-24.04"
        fi
        ;;
    debian)
        SCANNER_DIR="debian-11"
        ;;
    rhel)
        if [[ "$VERSION" == 8* ]]; then
            SCANNER_DIR="rhel-8"
        elif [[ "$VERSION" == 9* ]]; then
            SCANNER_DIR="rhel-9"
        else
            echo "RHEL version $VERSION not yet supported"
            error_exit "Unsupported RHEL version: $VERSION"
        fi
        ;;
    centos)
        SCANNER_DIR="centos-7"
        ;;
    *)
        echo "Distribution $DISTRO not yet supported"
        echo "Available distributions:"
        find . -maxdepth 1 -type d -name "*ubuntu*" -o -name "*debian*" -o -name "*rhel*" -o -name "*centos*" | sed 's|./||' | sort
        exit 1
        ;;
esac

if [ ! -d "$SCANNER_DIR" ]; then
    echo "Scanner directory $SCANNER_DIR not found"
    echo "Available directories:"
    find . -maxdepth 1 -type d -name "*ubuntu*" -o -name "*debian*" -o -name "*rhel*" -o -name "*centos*" | sed 's|./||' | sort
    exit 1
fi

echo "Using scanner: $SCANNER_DIR"

# Make scripts executable
if [ -d "$SCANNER_DIR/scripts" ]; then
    find "$SCANNER_DIR/scripts" -name "*.py" -type f -exec chmod +x {} \;
fi

# Create reports directory
mkdir -p "$SCANNER_DIR/reports"

echo ""
echo "Setup completed successfully!"
echo ""
echo "To run the scanner:"
echo "  cd $SCANNER_DIR"
echo "  sudo python3 scripts/vijenex-cis.py"
echo ""
echo "For help:"
echo "  python3 scripts/vijenex-cis.py --help"
echo ""
echo "Test basic functionality (no root required):"
if [ -f "$SCANNER_DIR/scripts/test-scanner.py" ]; then
    echo "  python3 scripts/test-scanner.py"
else
    echo "  python3 scripts/vijenex-cis.py --help"
fi