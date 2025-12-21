#!/bin/bash
# Verify that the scanner binary includes the latest fixes

echo "=== Scanner Binary Verification ==="
echo ""

BINARY=""
if [ -f "./bin/vijenex-cis-amd64" ]; then
    BINARY="./bin/vijenex-cis-amd64"
elif [ -f "./vijenex-cis-amd64" ]; then
    BINARY="./vijenex-cis-amd64"
else
    echo "❌ Binary not found. Run ./build.sh first"
    exit 1
fi

echo "Binary: $BINARY"
echo "Size: $(ls -lh "$BINARY" | awk '{print $5}')"
echo "Modified: $(ls -l "$BINARY" | awk '{print $6, $7, $8}')"
echo ""

# Check if binary contains debug string
if strings "$BINARY" | grep -q "\[DEBUG\]"; then
    echo "✅ Binary contains debug code (latest version)"
else
    echo "❌ Binary does NOT contain debug code (OLD VERSION)"
    echo "   You need to rebuild: ./build.sh"
fi

# Check if binary contains the new type handlers
if strings "$BINARY" | grep -q "PackageInstalled.*Package.*MultiPackage"; then
    echo "✅ Binary contains new type handlers"
else
    echo "⚠️  Cannot verify type handlers (may still be correct)"
fi

echo ""
echo "To rebuild:"
echo "  rm -f bin/* && ./build.sh"
