#!/bin/bash
# Local Vijenex CIS Scanner Runner
# For running directly from downloaded release without system installation

set -euo pipefail

# Colors
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
echo -e "${YELLOW}           Local Execution Mode${RESET}"
echo

# Detect Ubuntu version
if [ -f /etc/os-release ]; then
    . /etc/os-release
    UBUNTU_VERSION="${VERSION_ID:-unknown}"
else
    UBUNTU_VERSION="unknown"
fi

echo -e "${BLUE}🐧 Detected Ubuntu: ${UBUNTU_VERSION}${RESET}"

# Determine scanner directory
if [ -d "ubuntu-${UBUNTU_VERSION}" ]; then
    SCANNER_DIR="ubuntu-${UBUNTU_VERSION}"
elif [ -d "ubuntu-24.04" ]; then
    SCANNER_DIR="ubuntu-24.04"
    echo -e "${YELLOW}⚠ Using Ubuntu 24.04 scanner as fallback${RESET}"
elif [ -d "ubuntu-22.04" ]; then
    SCANNER_DIR="ubuntu-22.04"
    echo -e "${YELLOW}⚠ Using Ubuntu 22.04 scanner as fallback${RESET}"
else
    echo -e "${RED}❌ No compatible scanner found${RESET}"
    exit 1
fi

echo -e "${GREEN}✓ Using scanner: ${SCANNER_DIR}${RESET}"

# Clean any existing reports directories
find . -name "reports" -type d -exec rm -rf {} + 2>/dev/null || true

# Create local reports directory
mkdir -p "./reports"

echo -e "${CYAN}🚀 Starting CIS scan...${RESET}"
echo

# Run scanner with local output
cd "${SCANNER_DIR}"
exec python3 scripts/vijenex-cis.py --output-dir "../reports" "$@"