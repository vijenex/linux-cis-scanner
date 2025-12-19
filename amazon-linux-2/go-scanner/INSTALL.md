# Installing Vijenex CIS Scanner (No Go Required)

## Quick Start - Use Pre-built Binary

The scanner is a **standalone binary** - no Go, Python, or any dependencies needed!

### Option 1: Use Pre-built Binary (Recommended)

```bash
# 1. Download the pre-built binary for your architecture
#    (Get from releases or build on another machine)

# 2. Copy to your server
scp vijenex-cis-amd64 user@server:/tmp/

# 3. Make executable and run
ssh user@server
sudo chmod +x /tmp/vijenex-cis-amd64
sudo /tmp/vijenex-cis-amd64 --output-dir /tmp/scan-results
```

### Option 2: Use Smart Wrapper Script

The `vijenex-cis` wrapper script automatically:
- ✅ Uses pre-built binary if available (no Go needed)
- ✅ Builds automatically if Go is installed
- ✅ Shows clear instructions if neither is available

```bash
# Make wrapper executable
chmod +x vijenex-cis

# Run (will auto-detect binary or build)
sudo ./vijenex-cis --output-dir /tmp/scan-results
```

### Option 3: Build Binary (Requires Go)

If you have Go installed, you can build the binary:

```bash
# Build for current architecture
./build.sh

# Binary will be in: bin/vijenex-cis-amd64 or bin/vijenex-cis-arm64
```

## Architecture Detection

The wrapper automatically detects your system architecture:
- **x86_64/amd64** → Uses `vijenex-cis-amd64`
- **aarch64/arm64** → Uses `vijenex-cis-arm64`

## Installation Locations

The wrapper checks for binaries in this order:
1. `./bin/vijenex-cis-amd64` (or arm64)
2. `./bin/vijenex-cis`
3. `./vijenex-cis-amd64` (or arm64)
4. `./vijenex-cis`
5. `/usr/local/bin/vijenex-cis`
6. System PATH

## System-Wide Installation

```bash
# Copy binary to system path
sudo cp bin/vijenex-cis-amd64 /usr/local/bin/vijenex-cis
sudo chmod +x /usr/local/bin/vijenex-cis

# Run from anywhere
sudo vijenex-cis --output-dir /tmp/scan-results
```

## Building Binaries for Distribution

If you want to build binaries for servers without Go:

```bash
# On a machine with Go installed:
cd amazon-linux-2/go-scanner
./build.sh

# This creates:
# - bin/vijenex-cis-amd64 (for x86_64 servers)
# - bin/vijenex-cis-arm64 (for ARM64 servers)

# Copy to servers:
scp bin/vijenex-cis-amd64 user@server:/usr/local/bin/vijenex-cis
```

## Troubleshooting

### "Binary not found" Error

**Solution:** You need a pre-built binary. Options:
1. Download from releases
2. Build on another machine with Go
3. Install Go and build locally

### "Permission denied" Error

**Solution:**
```bash
chmod +x vijenex-cis-amd64
# or
chmod +x bin/vijenex-cis-amd64
```

### "Go is not installed" Error

**Solution:** This is normal if you don't have Go. Use a pre-built binary instead:
- The `vijenex-cis` wrapper will show you where to get one
- Or copy a binary from another machine that has Go

## Benefits of Standalone Binary

✅ **Zero dependencies** - No Go, Python, or libraries needed  
✅ **Single file** - Just copy and run  
✅ **Fast** - Native compiled code  
✅ **Small** - ~10-15MB binary size  
✅ **Portable** - Works on any Linux system  
✅ **Production-ready** - No build tools needed on servers

