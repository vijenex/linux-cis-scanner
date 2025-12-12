# Vijenex CIS Scanner - Go Binary (No Dependencies)

## Zero Dependencies - Runs Anywhere

This is a **standalone binary** version of the RHEL 8 CIS scanner written in Go.

### Key Features

✅ **No Python required** - Compiled binary
✅ **No dependencies** - Single executable file
✅ **No installation** - Just copy and run
✅ **Production-safe** - Read-only operations
✅ **Fast** - Native compiled code
✅ **Small** - ~10MB binary size

## Quick Start

### Build Binary (On Your Mac/Dev Machine)

```bash
# Install Go if needed
# Download from: https://go.dev/dl/

# Build binary
./build.sh

# Binary created: bin/vijenex-cis
```

### Deploy to RHEL 8 Server

```bash
# Copy binary to server
scp bin/vijenex-cis user@rhel8-server:/tmp/

# SSH to server
ssh user@rhel8-server

# Run scanner (no Python needed!)
sudo /tmp/vijenex-cis --output-dir /tmp/scan-results
```

## Usage

```bash
# Basic scan
sudo ./vijenex-cis

# Custom output directory
sudo ./vijenex-cis --output-dir /var/log/security

# Level 2 profile
sudo ./vijenex-cis --profile Level2

# Specific milestones
sudo ./vijenex-cis --milestones milestone-1-1.json,milestone-2-1.json

# CSV only
sudo ./vijenex-cis --format csv

# Help
./vijenex-cis --help
```

## Building

### Prerequisites

- Go 1.21 or later
- Make (optional)

### Build Commands

```bash
# Build for Linux (RHEL 8)
make build-linux

# Or use build script
./build.sh

# Or manual build
GOOS=linux GOARCH=amd64 go build -o bin/vijenex-cis ./cmd
```

### Build for Multiple Platforms

```bash
# Linux AMD64 (RHEL 8)
GOOS=linux GOARCH=amd64 go build -o vijenex-cis-linux-amd64 ./cmd

# Linux ARM64
GOOS=linux GOARCH=arm64 go build -o vijenex-cis-linux-arm64 ./cmd
```

## Installation (Optional)

```bash
# Copy to system path
sudo cp bin/vijenex-cis /usr/local/bin/
sudo chmod +x /usr/local/bin/vijenex-cis

# Run from anywhere
sudo vijenex-cis
```

## Comparison: Python vs Go

| Feature | Python Scanner | Go Binary |
|---------|---------------|-----------|
| **Dependencies** | Python 3.6+ required | None |
| **Installation** | Need Python installed | Just copy binary |
| **Size** | ~100KB + Python | ~10MB standalone |
| **Speed** | Fast | Faster |
| **Portability** | Requires Python | Runs anywhere |
| **Production** | May not have Python | Always works |

## Architecture

```
go-scanner/
├── cmd/
│   └── main.go              # CLI entry point
├── internal/
│   ├── scanner/
│   │   └── scanner.go       # Core scanner logic
│   ├── controls/
│   │   ├── types.go         # Control definitions
│   │   └── checks.go        # Check implementations
│   └── report/
│       ├── csv.go           # CSV report generator
│       └── html.go          # HTML report generator
├── milestones/
│   ├── milestone-1-1.json   # Control definitions
│   └── ...
├── go.mod                   # Go dependencies
├── Makefile                 # Build automation
└── build.sh                 # Build script
```

## Development

```bash
# Install dependencies
go mod download

# Run locally
go run ./cmd --output-dir ./reports

# Run tests
go test -v ./...

# Format code
go fmt ./...

# Lint code
golangci-lint run
```

## Deployment Options

### Option 1: Copy Binary
```bash
scp bin/vijenex-cis user@server:/usr/local/bin/
```

### Option 2: Package in RPM
```bash
# Include binary in RPM package
# No Python dependency needed
```

### Option 3: Container
```bash
# Create minimal container with just the binary
FROM scratch
COPY vijenex-cis /
ENTRYPOINT ["/vijenex-cis"]
```

## Binary Size Optimization

Current binary is optimized with:
- `-ldflags="-s -w"` - Strip debug info
- Static linking - No external dependencies
- Minimal imports - Only what's needed

## Security

- Read-only operations
- No network calls
- No external dependencies
- Runs with minimal privileges
- Can be verified with checksums

## Troubleshooting

### Binary won't run
```bash
# Check if executable
chmod +x vijenex-cis

# Check architecture
file vijenex-cis
# Should show: ELF 64-bit LSB executable, x86-64
```

### Permission denied
```bash
# Run with sudo for complete scan
sudo ./vijenex-cis
```

### Milestones not found
```bash
# Binary looks for milestones/ in current directory
# Make sure to run from scanner directory
cd /path/to/scanner
./vijenex-cis
```

## Next Steps

1. Build binary: `./build.sh`
2. Copy to RHEL 8 server
3. Run scan: `sudo ./vijenex-cis`
4. Review reports

## Support

For issues or questions:
- GitHub: https://github.com/vijenex/linux-cis-scanner
- Email: support@vijenex.com
