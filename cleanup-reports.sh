#!/bin/bash
# Remove all existing reports directories
find . -name "reports" -type d -exec rm -rf {} + 2>/dev/null || true
echo "All reports directories cleaned"