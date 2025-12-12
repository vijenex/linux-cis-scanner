#!/bin/bash
# Build standalone binary for RHEL 8

set -e

echo "=========================================="
echo "  Building Vijenex CIS Scanner (Go)"
echo "=========================================="

# Check Go installation
if ! command -v go &> /dev/null; then
    echo "❌ Go is not installed"
    echo "Install from: https://go.dev/dl/"
    exit 1
fi

echo "✓ Go version: $(go version)"

# Create bin directory
mkdir -p bin

# Download dependencies
echo "📦 Downloading dependencies..."
go mod download
go mod tidy

# Build for Linux AMD64 (RHEL 8)
echo "🔨 Building for Linux AMD64..."
GOOS=linux GOARCH=amd64 go build -ldflags="-s -w" -o bin/vijenex-cis ./cmd

# Make executable
chmod +x bin/vijenex-cis

# Get binary size
SIZE=$(du -h bin/vijenex-cis | cut -f1)

echo "=========================================="
echo "✅ Build complete!"
echo "=========================================="
echo "Binary: bin/vijenex-cis"
echo "Size: $SIZE"
echo "Platform: Linux AMD64"
echo ""
echo "Copy to RHEL 8 server:"
echo "  scp bin/vijenex-cis user@server:/usr/local/bin/"
echo ""
echo "Run on server:"
echo "  sudo vijenex-cis --output-dir /tmp/scan-results"
echo "=========================================="
