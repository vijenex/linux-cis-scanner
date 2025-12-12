#!/bin/bash
# Vijenex CIS Scanner Wrapper with OS Detection for Ubuntu/Debian

set -euo pipefail

# Detect Ubuntu/Debian version
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS_ID="${ID:-unknown}"
    OS_VERSION="${VERSION_ID:-unknown}"
else
    echo "Error: Cannot detect OS version"
    exit 1
fi

# Determine scanner directory based on Ubuntu version
if [ -d "/usr/share/vijenex-cis/ubuntu-${OS_VERSION}" ]; then
    SCANNER_DIR="/usr/share/vijenex-cis/ubuntu-${OS_VERSION}"
elif [ -d "/usr/share/vijenex-cis/ubuntu-24.04" ]; then
    SCANNER_DIR="/usr/share/vijenex-cis/ubuntu-24.04"
elif [ -d "/usr/share/vijenex-cis/ubuntu-22.04" ]; then
    SCANNER_DIR="/usr/share/vijenex-cis/ubuntu-22.04"
elif [ -d "/usr/share/vijenex-cis/debian-11" ]; then
    SCANNER_DIR="/usr/share/vijenex-cis/debian-11"
else
    echo "Error: No compatible scanner found for ${OS_ID} ${OS_VERSION}"
    exit 1
fi

# Check if user provided custom output directory
CUSTOM_OUTPUT=false
for arg in "$@"; do
    if [[ "$arg" == "--output-dir" ]] || [[ "$arg" == "--output" ]]; then
        CUSTOM_OUTPUT=true
        break
    fi
done

# Use system directory only if no custom output specified
if [ "$CUSTOM_OUTPUT" = false ]; then
    mkdir -p "/var/log/vijenex-cis/${OS_ID}-${OS_VERSION}-reports"
    OUTPUT_ARG="--output-dir /var/log/vijenex-cis/${OS_ID}-${OS_VERSION}-reports"
else
    OUTPUT_ARG=""
fi

# Run scanner
cd "${SCANNER_DIR}"
exec python3 scripts/vijenex-cis.py $OUTPUT_ARG "$@"
