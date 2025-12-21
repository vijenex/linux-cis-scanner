#!/bin/bash
# Install Go on EC2 for building the scanner
# This script installs Go without requiring root for the user directory

set -e

echo "=========================================="
echo "  Installing Go for Vijenex CIS Scanner"
echo "=========================================="

# Detect architecture
ARCH=$(uname -m)
case "$ARCH" in
    x86_64|amd64)
        GO_ARCH="amd64"
        ;;
    aarch64|arm64)
        GO_ARCH="arm64"
        ;;
    *)
        echo "❌ Unsupported architecture: $ARCH"
        exit 1
        ;;
esac

# Go version
GO_VERSION="1.21.5"
GO_TAR="go${GO_VERSION}.linux-${GO_ARCH}.tar.gz"
GO_URL="https://go.dev/dl/${GO_TAR}"

# Installation directory (user's home)
INSTALL_DIR="$HOME/go"
GO_ROOT="$INSTALL_DIR/go"

echo "📦 Architecture: $ARCH"
echo "📦 Go version: $GO_VERSION"
echo "📦 Install directory: $INSTALL_DIR"
echo ""

# Check if Go is already installed
if [ -d "$GO_ROOT" ] && [ -f "$GO_ROOT/bin/go" ]; then
    echo "✅ Go is already installed at $GO_ROOT"
    echo "   Version: $($GO_ROOT/bin/go version 2>/dev/null || echo 'unknown')"
    echo ""
    echo "To use it, add to your PATH:"
    echo "  export PATH=\$PATH:$GO_ROOT/bin"
    echo "  export GOPATH=\$HOME/go"
    echo ""
    read -p "Reinstall? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 0
    fi
    echo "🗑️  Removing old installation..."
    rm -rf "$GO_ROOT"
fi

# Create install directory
mkdir -p "$INSTALL_DIR"
cd "$INSTALL_DIR"

# Download Go
echo "📥 Downloading Go..."
if command -v wget &> /dev/null; then
    wget "$GO_URL" -O "$GO_TAR"
elif command -v curl &> /dev/null; then
    curl -L "$GO_URL" -o "$GO_TAR"
else
    echo "❌ Neither wget nor curl found. Please install one of them."
    exit 1
fi

# Extract
echo "📦 Extracting Go..."
tar -xzf "$GO_TAR"
rm "$GO_TAR"

# Verify installation
if [ -f "$GO_ROOT/bin/go" ]; then
    echo "✅ Go installed successfully!"
    echo ""
    echo "📋 To use Go, add these to your ~/.bashrc or run them now:"
    echo ""
    echo "  export PATH=\$PATH:$GO_ROOT/bin"
    echo "  export GOPATH=\$HOME/go"
    echo ""
    echo "Or run this command:"
    echo "  export PATH=\$PATH:$GO_ROOT/bin && export GOPATH=\$HOME/go && $GO_ROOT/bin/go version"
    echo ""
    echo "🔨 Now you can build the scanner:"
    echo "  cd ~/linux-cis-scanner/ubuntu-24.04/go-scanner"
    echo "  export PATH=\$PATH:$GO_ROOT/bin"
    echo "  ./build.sh"
else
    echo "❌ Installation failed - go binary not found"
    exit 1
fi

