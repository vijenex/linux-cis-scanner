#!/bin/bash

# Vijenex CIS Scanner Installation Script
# Creates system-wide vijenex-cis command

set -e

echo "Installing Vijenex CIS Scanner..."

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   echo "This script must be run as root (use sudo)" 
   exit 1
fi

# Get the current directory
CURRENT_DIR="$(pwd)"

# Create symbolic link in /usr/local/bin
ln -sf "$CURRENT_DIR/ubuntu-24.04/scripts/vijenex-cis.py" /usr/local/bin/vijenex-cis
chmod +x /usr/local/bin/vijenex-cis

echo "✓ Vijenex CIS Scanner installed successfully!"
echo "✓ You can now run: vijenex-cis --help"
echo "✓ Example usage: vijenex-cis --sections 1,2,3"