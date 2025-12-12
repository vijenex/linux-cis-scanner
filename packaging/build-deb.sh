#!/bin/bash
# Build DEB package for Ubuntu/Debian

set -euo pipefail

VERSION="1.0.0"
PACKAGE_NAME="vijenex-cis-scanner"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BOLD='\033[1m'
RESET='\033[0m'

echo -e "${BOLD}${BLUE}Building DEB Package for Vijenex CIS Scanner${RESET}"
echo "============================================================"

# Check for required tools
if ! command -v dpkg-deb >/dev/null 2>&1; then
    echo -e "${RED}Error: dpkg-deb not found${RESET}"
    echo "Install with: sudo apt install dpkg-dev"
    exit 1
fi

# Create build directory
BUILD_DIR="packaging/deb/build/${PACKAGE_NAME}_${VERSION}"
echo -e "${BLUE}Creating build directory...${RESET}"
rm -rf "${BUILD_DIR}"
mkdir -p "${BUILD_DIR}"

# Create directory structure
echo -e "${BLUE}Setting up package structure...${RESET}"
mkdir -p "${BUILD_DIR}/usr/bin"
mkdir -p "${BUILD_DIR}/usr/share/vijenex-cis"
mkdir -p "${BUILD_DIR}/etc/vijenex-cis"
mkdir -p "${BUILD_DIR}/var/log/vijenex-cis"
mkdir -p "${BUILD_DIR}/usr/share/man/man1"
mkdir -p "${BUILD_DIR}/DEBIAN"

# Copy scanner components
echo -e "${BLUE}Copying scanner components...${RESET}"
for distro_dir in ubuntu-20.04 ubuntu-22.04 ubuntu-24.04 debian-11; do
    if [ -d "$distro_dir" ]; then
        cp -r "$distro_dir" "${BUILD_DIR}/usr/share/vijenex-cis/"
        echo -e "${GREEN}✓ $distro_dir${RESET}"
    fi
done

# Install wrapper script
echo -e "${BLUE}Installing wrapper script...${RESET}"
install -m 0755 packaging/deb/vijenex-cis-wrapper.sh "${BUILD_DIR}/usr/bin/vijenex-cis"

# Install documentation
cp LICENSE "${BUILD_DIR}/usr/share/vijenex-cis/"
cp README.md "${BUILD_DIR}/usr/share/vijenex-cis/"

# Install man page
install -m 0644 packaging/vijenex-cis.1 "${BUILD_DIR}/usr/share/man/man1/vijenex-cis.1"
gzip -9 "${BUILD_DIR}/usr/share/man/man1/vijenex-cis.1"

# Create DEBIAN control files
echo -e "${BLUE}Creating control files...${RESET}"
cp packaging/deb/control "${BUILD_DIR}/DEBIAN/"
cp packaging/deb/postinst "${BUILD_DIR}/DEBIAN/"
chmod 0755 "${BUILD_DIR}/DEBIAN/postinst"

# Build package
echo -e "${BLUE}Building DEB package...${RESET}"
mkdir -p packaging/deb/dist
dpkg-deb --build "${BUILD_DIR}" "packaging/deb/dist/${PACKAGE_NAME}_${VERSION}_all.deb"

# Cleanup
rm -rf "${BUILD_DIR}"

echo "============================================================"
echo -e "${GREEN}${BOLD}✅ DEB package built successfully!${RESET}"
echo -e "${GREEN}Location: packaging/deb/dist/${RESET}"
ls -lh packaging/deb/dist/
echo "============================================================"
echo -e "${YELLOW}Install with:${RESET}"
echo "  sudo dpkg -i packaging/deb/dist/${PACKAGE_NAME}_${VERSION}_all.deb"
echo "  or"
echo "  sudo apt install ./packaging/deb/dist/${PACKAGE_NAME}_${VERSION}_all.deb"
