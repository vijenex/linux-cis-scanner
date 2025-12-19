# Quick Start - Run Without Go

## ✅ Solution: Smart Wrapper Script

The `vijenex-cis` wrapper script works **without Go** if you have a pre-built binary.

## How It Works

```bash
# 1. Make wrapper executable
chmod +x vijenex-cis

# 2. Run it (no Go needed if binary exists)
sudo ./vijenex-cis --output-dir /tmp/scan-results
```

The wrapper will:
1. ✅ **First**: Look for pre-built binary (no Go needed!)
2. ✅ **Second**: Try to build if Go is available
3. ✅ **Third**: Show instructions if neither is available

## Getting a Pre-built Binary

### Option A: Build on Your Mac/Dev Machine

```bash
# On your Mac (with Go installed):
cd linux-cis-scanner/amazon-linux-2/go-scanner
./build.sh

# This creates:
# - bin/vijenex-cis-amd64 (for x86_64 servers)
# - bin/vijenex-cis-arm64 (for ARM64 servers)
```

### Option B: Copy Binary to Server

```bash
# From your Mac:
scp bin/vijenex-cis-amd64 user@server:/path/to/linux-cis-scanner/amazon-linux-2/go-scanner/bin/

# On server:
cd linux-cis-scanner/amazon-linux-2/go-scanner
chmod +x vijenex-cis
sudo ./vijenex-cis
```

### Option C: Use Binary Anywhere

```bash
# Copy to system path
sudo cp bin/vijenex-cis-amd64 /usr/local/bin/vijenex-cis
sudo chmod +x /usr/local/bin/vijenex-cis

# Run from anywhere
sudo vijenex-cis --output-dir /tmp/scan-results
```

## What the Wrapper Checks

The wrapper looks for binaries in this order:
1. `./bin/vijenex-cis-amd64` (or `-arm64` based on your architecture)
2. `./bin/vijenex-cis`
3. `./vijenex-cis-amd64` (or `-arm64`)
4. `./vijenex-cis`
5. `/usr/local/bin/vijenex-cis`
6. System PATH

## Example: Server Without Go

```bash
# On server (no Go installed):
[root@server go-scanner]# ./vijenex-cis
❌ Vijenex CIS Scanner binary not found

📋 To get the scanner running:

Option 1: Use pre-built binary (Recommended)
  # Download pre-built binary for x86_64:
  # Place it in: /path/to/go-scanner/bin/vijenex-cis-amd64
  chmod +x /path/to/go-scanner/bin/vijenex-cis-amd64

Option 2: Build on another machine with Go
  # On a machine with Go installed:
  cd /path/to/go-scanner
  ./build.sh
  # Then copy bin/vijenex-cis-amd64 to this server
```

## Summary

✅ **No Go needed** - Just use pre-built binary  
✅ **Smart detection** - Wrapper finds binary automatically  
✅ **Auto-build** - Builds if Go is available  
✅ **Clear errors** - Shows exactly what to do  

**Next Step**: Build binary on a machine with Go, then copy to your server!

