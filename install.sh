#!/bin/bash

# Vijenex CIS Scanner Installation Script
# Enterprise-grade installation like OpenSCAP

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
RESET='\033[0m'

# Display banner
echo -e "${CYAN}${BOLD}"
echo "██╗   ██╗██╗     ██╗███████╗███╗   ██╗███████╗██╗  ██╗"
echo "██║   ██║██║     ██║██╔════╝████╗  ██║██╔════╝╚██╗██╔╝"
echo "██║   ██║██║     ██║█████╗  ██╔██╗ ██║█████╗   ╚███╔╝ "
echo "╚██╗ ██╔╝██║██   ██║██╔══╝  ██║╚██╗██║██╔══╝   ██╔██╗ "
echo " ╚████╔╝ ██║╚█████╔╝███████╗██║ ╚████║███████╗██╔╝ ██╗"
echo "  ╚═══╝  ╚═╝ ╚════╝ ╚══════╝╚═╝  ╚═══╝╚══════╝╚═╝  ╚═╝"
echo -e "${RESET}"
echo -e "${BOLD}${BLUE}                 Vijenex CIS Scanner${RESET}"
echo -e "${YELLOW}           Enterprise Linux Security Compliance${RESET}"
echo -e "${CYAN}═══════════════════════════════════════════════════════════${RESET}"

echo -e "${BOLD}🚀 Installing Vijenex CIS Scanner...${RESET}"

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   echo -e "${RED}❌ Error: This script must be run as root${RESET}"
   echo -e "${YELLOW}💡 Usage: sudo ./install.sh${RESET}"
   exit 1
fi

# Detect distribution
if [ -f /etc/os-release ]; then
    # shellcheck source=/etc/os-release
    . /etc/os-release
    DISTRO="${ID:-unknown}"
    VERSION="${VERSION_ID:-unknown}"
else
    echo -e "${RED}❌ Cannot detect Linux distribution${RESET}"
    exit 1
fi

echo -e "${BLUE}🐧 Detected: $PRETTY_NAME${RESET}"

# Check Python 3
if ! command -v python3 >/dev/null 2>&1; then
    echo -e "${RED}❌ Python 3 is required but not installed${RESET}"
    echo -e "${YELLOW}💡 Install with: apt install python3 (Ubuntu/Debian) or yum install python3 (RHEL/CentOS)${RESET}"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
echo -e "${GREEN}✓ Python ${PYTHON_VERSION} found${RESET}"

# Get installation directory
INSTALL_DIR="$(pwd)"
echo -e "${BLUE}📁 Installation directory: ${INSTALL_DIR}${RESET}"

# Create directories
mkdir -p /etc/vijenex-cis
mkdir -p /var/log/vijenex-cis
mkdir -p /usr/share/vijenex-cis

# Copy all Ubuntu versions to preserve OS-specific structure
echo -e "${YELLOW}📋 Installing scanner components...${RESET}"
for ubuntu_dir in ubuntu-*/; do
    if [ -d "$ubuntu_dir" ]; then
        ubuntu_name=$(basename "$ubuntu_dir")
        cp -r "$ubuntu_dir" "/usr/share/vijenex-cis/$ubuntu_name"
        echo -e "${GREEN}✓ $ubuntu_name scanner installed${RESET}"
    fi
done

# Detect current Ubuntu version for wrapper script
if [[ "${VERSION_ID:-}" == "24.04" ]] && [ -d "/usr/share/vijenex-cis/ubuntu-24.04" ]; then
    SCANNER_VERSION="ubuntu-24.04"
elif [[ "${VERSION_ID:-}" == "22.04" ]] && [ -d "/usr/share/vijenex-cis/ubuntu-22.04" ]; then
    SCANNER_VERSION="ubuntu-22.04"
elif [[ "${VERSION_ID:-}" == "20.04" ]] && [ -d "/usr/share/vijenex-cis/ubuntu-20.04" ]; then
    SCANNER_VERSION="ubuntu-20.04"
else
    echo -e "${YELLOW}⚠ Unsupported Ubuntu version: ${VERSION_ID:-unknown}${RESET}"
    if [ -d "/usr/share/vijenex-cis/ubuntu-24.04" ]; then
        SCANNER_VERSION="ubuntu-24.04"
        echo -e "${YELLOW}📋 Using Ubuntu 24.04 scanner as fallback${RESET}"
    elif [ -d "/usr/share/vijenex-cis/ubuntu-22.04" ]; then
        SCANNER_VERSION="ubuntu-22.04"
        echo -e "${YELLOW}📋 Using Ubuntu 22.04 scanner as fallback${RESET}"
    else
        echo -e "${RED}❌ No compatible scanner found${RESET}"
        exit 1
    fi
fi
if [ -f "LICENSE" ]; then
    cp LICENSE /usr/share/vijenex-cis/
fi
if [ -f "README.md" ]; then
    cp README.md /usr/share/vijenex-cis/
fi

# Clean any existing reports directories first
find . -name "reports" -type d -exec rm -rf {} + 2>/dev/null || true

# Create wrapper script with OS detection
cat > /usr/local/bin/vijenex-cis << EOF
#!/bin/bash
# Vijenex CIS Scanner Wrapper with OS Detection

# Detect Ubuntu version
if [ -f /etc/os-release ]; then
    . /etc/os-release
    UBUNTU_VERSION="\${VERSION_ID:-unknown}"
else
    UBUNTU_VERSION="unknown"
fi

# Determine scanner directory
if [ -d "/usr/share/vijenex-cis/ubuntu-\${UBUNTU_VERSION}" ]; then
    SCANNER_DIR="/usr/share/vijenex-cis/ubuntu-\${UBUNTU_VERSION}"
elif [ -d "/usr/share/vijenex-cis/ubuntu-24.04" ]; then
    SCANNER_DIR="/usr/share/vijenex-cis/ubuntu-24.04"
elif [ -d "/usr/share/vijenex-cis/ubuntu-22.04" ]; then
    SCANNER_DIR="/usr/share/vijenex-cis/ubuntu-22.04"
else
    echo "Error: No compatible scanner found"
    exit 1
fi

# Clean any existing reports directories
find /usr/share/vijenex-cis -name "reports" -type d -exec rm -rf {} + 2>/dev/null || true

# Create single OS-specific reports directory
mkdir -p "/var/log/vijenex-cis/ubuntu-\${UBUNTU_VERSION}-reports"

# Run scanner with OS-specific output directory
cd "\${SCANNER_DIR}"
exec python3 scripts/vijenex-cis.py --output-dir "/var/log/vijenex-cis/ubuntu-\${UBUNTU_VERSION}-reports" "\$@"
EOF

# Make executable
chmod +x /usr/local/bin/vijenex-cis
chmod +x /usr/share/vijenex-cis/*/scripts/*.py

# Create man page
cat > /usr/share/man/man1/vijenex-cis.1 << 'EOF'
.TH VIJENEX-CIS 1 "November 2024" "1.0.0" "Vijenex CIS Scanner"
.SH NAME
vijenex-cis \- Enterprise Linux Security Compliance Scanner
.SH SYNOPSIS
.B vijenex-cis
[\fIOPTIONS\fR]
.SH DESCRIPTION
Vijenex CIS Scanner is an enterprise-grade security compliance auditing tool for Linux systems based on CIS (Center for Internet Security) benchmarks.
.SH OPTIONS
.TP
\fB\-\-profile\fR LEVEL
Set CIS profile level (Level1, Level2). Default: Level1
.TP
\fB\-\-output\fR DIR
Output directory for reports. Default: ./reports
.TP
\fB\-\-format\fR FORMAT
Report format (html, csv, both). Default: both
.TP
\fB\-\-help\fR
Show help message
.SH EXAMPLES
.TP
sudo vijenex-cis
Run complete CIS compliance scan
.TP
sudo vijenex-cis --profile Level2 --output /var/log/security
Run Level 2 scan with custom output directory
.SH AUTHOR
Vijenex Security Platform
.SH SEE ALSO
OpenSCAP, CIS Benchmarks
EOF

# Update man database
if command -v mandb >/dev/null 2>&1; then
    if ! mandb -q 2>/dev/null; then
        echo -e "${YELLOW}⚠ Warning: Failed to update man database${RESET}" >&2
    else
        echo -e "${GREEN}✓ Man database updated${RESET}"
    fi
else
    echo -e "${YELLOW}⚠ Warning: mandb command not found, skipping man database update${RESET}" >&2
fi

echo -e "${CYAN}═══════════════════════════════════════════════════════════${RESET}"
echo -e "${GREEN}${BOLD}✅ Vijenex CIS Scanner installed successfully!${RESET}"
echo -e "${GREEN}✓ Command available: ${BOLD}vijenex-cis${RESET}"
echo -e "${GREEN}✓ Man page: ${BOLD}man vijenex-cis${RESET}"
echo -e "${GREEN}✓ OS-specific reports: ${BOLD}/var/log/vijenex-cis/ubuntu-${VERSION_ID:-unknown}-reports/${RESET}"
echo -e "${CYAN}═══════════════════════════════════════════════════════════${RESET}"
echo -e "${YELLOW}💡 Usage Examples:${RESET}"
echo -e "   ${BOLD}sudo vijenex-cis${RESET}                    # Complete scan"
echo -e "   ${BOLD}sudo vijenex-cis --profile Level2${RESET}   # Level 2 scan"
echo -e "   ${BOLD}vijenex-cis --help${RESET}                 # Show help"
echo -e "   ${BOLD}man vijenex-cis${RESET}                    # Manual page"
echo -e "${CYAN}═══════════════════════════════════════════════════════════${RESET}"