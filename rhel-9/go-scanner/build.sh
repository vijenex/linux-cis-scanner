#!/bin/bash
set -e

echo "Building Vijenex CIS Scanner for RHEL 9..."

mkdir -p bin

go mod download
go build -o bin/vijenex-cis cmd/main.go

echo "Build complete: bin/vijenex-cis"
