#!/bin/bash
# Build standalone binary for Ubuntu 24.04 LTS
# This script requires Go to be installed

set -e

echo "=========================================="
echo "  Building Vijenex CIS Scanner (Go)"
echo "  Ubuntu 24.04 LTS"
echo "=========================================="

# Check Go installation
if ! command -v go &> /dev/null; then
    echo "❌ Go is not installed"
    echo ""
    echo "📋 To build the binary:"
    echo "  1. Install Go from: https://go.dev/dl/"
    echo "  2. Or use pre-built binary (no Go needed)"
    echo ""
    echo "💡 Tip: Use './vijenex-cis' wrapper script which will:"
    echo "  - Use pre-built binary if available (no Go needed)"
    echo "  - Build automatically if Go is installed"
    echo "  - Show instructions if neither is available"
    echo ""
    exit 1
fi

echo "✓ Go version: $(go version)"

# Create bin directory
mkdir -p bin

# Download dependencies
echo "📦 Downloading dependencies..."
go mod download
go mod tidy

# Build for Linux AMD64 (x86_64)
echo "🔨 Building for Linux AMD64..."
GOOS=linux GOARCH=amd64 go build -ldflags="-s -w" -o bin/vijenex-cis-amd64 ./cmd
chmod +x bin/vijenex-cis-amd64

# Build for Linux ARM64 (aarch64)
echo "🔨 Building for Linux ARM64..."
GOOS=linux GOARCH=arm64 go build -ldflags="-s -w" -o bin/vijenex-cis-arm64 ./cmd
chmod +x bin/vijenex-cis-arm64

# Get binary sizes
SIZE_AMD64=$(du -h bin/vijenex-cis-amd64 | cut -f1)
SIZE_ARM64=$(du -h bin/vijenex-cis-arm64 | cut -f1)

echo "=========================================="
echo "✅ Build complete!"
echo "=========================================="
echo "AMD64 Binary: bin/vijenex-cis-amd64 ($SIZE_AMD64)"
echo "ARM64 Binary: bin/vijenex-cis-arm64 ($SIZE_ARM64)"
echo ""
echo "Copy to Ubuntu 24.04 server:"
echo "  # For x86_64:"
echo "  scp bin/vijenex-cis-amd64 user@server:/usr/local/bin/vijenex-cis"
echo "  # For aarch64:"
echo "  scp bin/vijenex-cis-arm64 user@server:/usr/local/bin/vijenex-cis"
echo ""
echo "Run on server:"
echo "  sudo vijenex-cis --output-dir /tmp/scan-results"
echo "=========================================="

