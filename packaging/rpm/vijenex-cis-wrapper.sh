#!/bin/bash
# Vijenex CIS Scanner Wrapper with OS Detection

set -euo pipefail

# Detect RHEL/CentOS version
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS_ID="${ID:-unknown}"
    OS_VERSION="${VERSION_ID:-unknown}"
else
    echo "Error: Cannot detect OS version"
    exit 1
fi

# Determine scanner directory based on OS
case "${OS_ID}" in
    rhel)
        if [ -d "/usr/share/vijenex-cis/rhel-${OS_VERSION%%.*}" ]; then
            SCANNER_DIR="/usr/share/vijenex-cis/rhel-${OS_VERSION%%.*}"
        elif [ -d "/usr/share/vijenex-cis/rhel-8" ]; then
            SCANNER_DIR="/usr/share/vijenex-cis/rhel-8"
        else
            echo "Error: No compatible RHEL scanner found"
            exit 1
        fi
        ;;
    centos)
        if [ -d "/usr/share/vijenex-cis/centos-${OS_VERSION%%.*}" ]; then
            SCANNER_DIR="/usr/share/vijenex-cis/centos-${OS_VERSION%%.*}"
        elif [ -d "/usr/share/vijenex-cis/centos-7" ]; then
            SCANNER_DIR="/usr/share/vijenex-cis/centos-7"
        else
            echo "Error: No compatible CentOS scanner found"
            exit 1
        fi
        ;;
    *)
        echo "Error: Unsupported OS: ${OS_ID}"
        exit 1
        ;;
esac

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
    mkdir -p "/var/log/vijenex-cis/${OS_ID}-${OS_VERSION%%.*}-reports"
    OUTPUT_ARG="--output-dir /var/log/vijenex-cis/${OS_ID}-${OS_VERSION%%.*}-reports"
else
    OUTPUT_ARG=""
fi

# Run scanner
cd "${SCANNER_DIR}"
exec python3 scripts/vijenex-cis.py $OUTPUT_ARG "$@"
