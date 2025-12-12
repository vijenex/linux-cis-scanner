#!/bin/bash
#
# Vijenex CIS Scanner - RHEL 8
# Auto-detects Python or Go and runs the scanner
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║           VIJENEX CIS SCANNER - RHEL 8                       ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}❌ Error: This script must be run as root${NC}"
    echo -e "${YELLOW}Please run: sudo ./scan.sh${NC}"
    exit 1
fi

# Check for Python 3
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
    PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
    PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)
    
    if [ "$PYTHON_MAJOR" -ge 3 ] && [ "$PYTHON_MINOR" -ge 6 ]; then
        echo -e "${GREEN}✓ Python $PYTHON_VERSION detected${NC}"
        echo -e "${BLUE}🚀 Running Python scanner...${NC}"
        echo ""
        
        python3 scripts/vijenex-cis.py --profile Level1 "$@"
        
        echo ""
        echo -e "${GREEN}✅ Scan completed!${NC}"
        echo -e "${YELLOW}📄 Reports generated in: ./reports/${NC}"
        echo -e "${YELLOW}   - HTML: reports/vijenex-cis-report.html${NC}"
        echo -e "${YELLOW}   - CSV:  reports/vijenex-cis-results.csv${NC}"
        exit 0
    else
        echo -e "${YELLOW}⚠ Python $PYTHON_VERSION found (need 3.6+)${NC}"
    fi
else
    echo -e "${YELLOW}⚠ Python 3 not found${NC}"
fi

# Check for Go binary
if [ -f "bin/vijenex-cis-scanner" ]; then
    echo -e "${GREEN}✓ Go binary detected${NC}"
    echo -e "${BLUE}🚀 Running Go scanner...${NC}"
    echo ""
    
    ./bin/vijenex-cis-scanner --profile Level1 "$@"
    
    echo ""
    echo -e "${GREEN}✅ Scan completed!${NC}"
    echo -e "${YELLOW}📄 Reports generated in: ./reports/${NC}"
    exit 0
fi

# Neither found
echo -e "${RED}❌ Error: No scanner found${NC}"
echo ""
echo -e "${YELLOW}Requirements:${NC}"
echo -e "  • Python 3.6+ OR"
echo -e "  • Go binary in bin/vijenex-cis-scanner"
echo ""
echo -e "${YELLOW}To install Python 3:${NC}"
echo -e "  sudo dnf install python3"
echo ""
exit 1
