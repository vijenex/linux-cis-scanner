#!/bin/bash
# Build RPM package for RHEL/CentOS

set -euo pipefail

VERSION="1.0.0"
RELEASE="1"
PACKAGE_NAME="vijenex-cis-scanner"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BOLD='\033[1m'
RESET='\033[0m'

echo -e "${BOLD}${BLUE}Building RPM Package for Vijenex CIS Scanner${RESET}"
echo "============================================================"

# Check if running on RHEL/CentOS
if [ ! -f /etc/redhat-release ]; then
    echo -e "${YELLOW}Warning: Not running on RHEL/CentOS. RPM build may fail.${RESET}"
fi

# Check for required tools
if ! command -v rpmbuild >/dev/null 2>&1; then
    echo -e "${RED}Error: rpmbuild not found${RESET}"
    echo "Install with: sudo yum install rpm-build"
    exit 1
fi

# Setup RPM build environment
echo -e "${BLUE}Setting up RPM build environment...${RESET}"
mkdir -p ~/rpmbuild/{BUILD,RPMS,SOURCES,SPECS,SRPMS}

# Create source tarball
echo -e "${BLUE}Creating source tarball...${RESET}"
cd ..
tar --exclude='./packaging' \
    --exclude='./.*' \
    --exclude='*.pyc' \
    --exclude='__pycache__' \
    --exclude='reports' \
    -czf ~/rpmbuild/SOURCES/${PACKAGE_NAME}-${VERSION}.tar.gz \
    --transform "s,^\.,${PACKAGE_NAME}-${VERSION}," \
    ./rhel-8 ./rhel-9 ./centos-7 ./LICENSE ./README.md ./packaging

# Copy spec file
echo -e "${BLUE}Copying spec file...${RESET}"
cp packaging/rpm/${PACKAGE_NAME}.spec ~/rpmbuild/SPECS/

# Build RPM
echo -e "${BLUE}Building RPM package...${RESET}"
rpmbuild -ba ~/rpmbuild/SPECS/${PACKAGE_NAME}.spec

# Copy built packages
echo -e "${BLUE}Copying packages to packaging/rpm/dist/...${RESET}"
mkdir -p packaging/rpm/dist
cp ~/rpmbuild/RPMS/noarch/${PACKAGE_NAME}-${VERSION}-${RELEASE}.*.rpm packaging/rpm/dist/
cp ~/rpmbuild/SRPMS/${PACKAGE_NAME}-${VERSION}-${RELEASE}.*.src.rpm packaging/rpm/dist/

echo "============================================================"
echo -e "${GREEN}${BOLD}✅ RPM package built successfully!${RESET}"
echo -e "${GREEN}Location: packaging/rpm/dist/${RESET}"
ls -lh packaging/rpm/dist/
echo "============================================================"
echo -e "${YELLOW}Install with:${RESET}"
echo "  sudo rpm -ivh packaging/rpm/dist/${PACKAGE_NAME}-${VERSION}-${RELEASE}.*.rpm"
echo "  or"
echo "  sudo yum localinstall packaging/rpm/dist/${PACKAGE_NAME}-${VERSION}-${RELEASE}.*.rpm"
