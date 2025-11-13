#!/bin/bash

# Vijenex CIS Scanner Installation Script
# Enterprise-grade installation like OpenSCAP

set -e

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
    . /etc/os-release
    DISTRO=$ID
    VERSION=$VERSION_ID
else
    echo -e "${RED}❌ Cannot detect Linux distribution${RESET}"
    exit 1
fi

echo -e "${BLUE}🐧 Detected: $PRETTY_NAME${RESET}"

# Check Python 3
if ! command -v python3 &> /dev/null; then
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

# Copy files
echo -e "${YELLOW}📋 Installing scanner components...${RESET}"
cp -r ubuntu-24.04/* /usr/share/vijenex-cis/
cp LICENSE /usr/share/vijenex-cis/
cp README.md /usr/share/vijenex-cis/

# Create wrapper script
cat > /usr/local/bin/vijenex-cis << 'EOF'
#!/bin/bash
# Vijenex CIS Scanner Wrapper
cd /usr/share/vijenex-cis
exec python3 scripts/vijenex-cis.py "$@"
EOF

# Make executable
chmod +x /usr/local/bin/vijenex-cis
chmod +x /usr/share/vijenex-cis/scripts/vijenex-cis.py

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
if command -v mandb &> /dev/null; then
    mandb -q 2>/dev/null || true
fi

echo -e "${CYAN}═══════════════════════════════════════════════════════════${RESET}"
echo -e "${GREEN}${BOLD}✅ Vijenex CIS Scanner installed successfully!${RESET}"
echo -e "${GREEN}✓ Command available: ${BOLD}vijenex-cis${RESET}"
echo -e "${GREEN}✓ Man page: ${BOLD}man vijenex-cis${RESET}"
echo -e "${GREEN}✓ Log directory: ${BOLD}/var/log/vijenex-cis${RESET}"
echo -e "${CYAN}═══════════════════════════════════════════════════════════${RESET}"
echo -e "${YELLOW}💡 Usage Examples:${RESET}"
echo -e "   ${BOLD}sudo vijenex-cis${RESET}                    # Complete scan"
echo -e "   ${BOLD}sudo vijenex-cis --profile Level2${RESET}   # Level 2 scan"
echo -e "   ${BOLD}vijenex-cis --help${RESET}                 # Show help"
echo -e "   ${BOLD}man vijenex-cis${RESET}                    # Manual page"
echo -e "${CYAN}═══════════════════════════════════════════════════════════${RESET}"