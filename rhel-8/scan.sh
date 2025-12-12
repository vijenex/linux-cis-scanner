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

# Check for Python 3 (try multiple commands)
PYTHON_CMD=""
for cmd in python3 python python3.6 python3.8 python3.9 python3.11; do
    if command -v $cmd &> /dev/null; then
        VERSION=$($cmd --version 2>&1 | grep -oP 'Python \K[0-9.]+')
        MAJOR=$(echo $VERSION | cut -d. -f1)
        MINOR=$(echo $VERSION | cut -d. -f2)
        
        if [ "$MAJOR" -eq 3 ] && [ "$MINOR" -ge 6 ]; then
            PYTHON_CMD=$cmd
            PYTHON_VERSION=$VERSION
            break
        fi
    fi
done

if [ -n "$PYTHON_CMD" ]; then
    echo -e "${GREEN}✓ Python $PYTHON_VERSION detected ($PYTHON_CMD)${NC}"
    echo -e "${BLUE}🚀 Running Python scanner...${NC}"
    echo ""
    
    $PYTHON_CMD scripts/vijenex-cis.py --profile Level1 "$@"
    
    echo ""
    echo -e "${GREEN}✅ Scan completed!${NC}"
    echo -e "${YELLOW}📄 Reports generated in: ./reports/${NC}"
    echo -e "${YELLOW}   - HTML: reports/vijenex-cis-report.html${NC}"
    echo -e "${YELLOW}   - CSV:  reports/vijenex-cis-results.csv${NC}"
    exit 0
else
    echo -e "${YELLOW}⚠ Python 3.6+ not found${NC}"
    echo -e "${YELLOW}   Tried: python3, python, python3.6, python3.8, python3.9, python3.11${NC}"
fi

# Check for Go binary (multiple locations)
GO_BINARY=""
for binary in ./vijenex-cis ./vijenex-cis-amd64 ./vijenex-cis-arm64 ./go-scanner/bin/vijenex-cis ./bin/vijenex-cis-scanner; do
    if [ -f "$binary" ] && [ -x "$binary" ]; then
        GO_BINARY="$binary"
        break
    fi
done

if [ -n "$GO_BINARY" ]; then
    echo -e "${GREEN}✓ Go binary detected: $GO_BINARY${NC}"
    echo -e "${BLUE}🚀 Running Go scanner...${NC}"
    echo ""
    
    $GO_BINARY "$@"
    
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
