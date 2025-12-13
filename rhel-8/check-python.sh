#!/bin/bash
# Debug script to check Python availability

echo "Checking Python installations..."
echo ""

for cmd in python python2 python3 python36 python38 python39 python3.6 python3.8 python3.9 python3.11 /usr/bin/python3 /usr/libexec/platform-python; do
    if command -v $cmd &> /dev/null; then
        version=$($cmd --version 2>&1)
        echo "✓ Found: $cmd -> $version"
    fi
done

echo ""
echo "Checking /usr/bin for python*:"
ls -la /usr/bin/python* 2>/dev/null || echo "No python* in /usr/bin"

echo ""
echo "Checking platform-python:"
ls -la /usr/libexec/platform-python 2>/dev/null || echo "No platform-python"
