# RHEL 8 CIS Scanner

## Smart Multi-Engine Scanner

This scanner automatically detects what's available on your system and lets you choose:

1. **Python Scanner** - Fast, feature-rich (requires Python 3.6+)
2. **Go Binary** - Standalone, no dependencies (requires building once)
3. **Shell Script** - Pure Bash, universal (coming soon)

## Quick Start

```bash
# Clone repository
git clone https://github.com/vijenex/linux-cis-scanner.git
cd linux-cis-scanner/rhel-8

# Run scanner (auto-detects available engines)
sudo ./vijenex-cis

# Or with options
sudo ./vijenex-cis --output-dir /tmp/scan-results --profile Level1
```

## How It Works

The launcher (`vijenex-cis`) automatically:
1. Detects which scanners are available
2. Shows you options
3. Lets you choose (or auto-selects if only one available)
4. Runs the selected scanner

## Scanner Options

### Option 1: Python Scanner (Default)

**Requirements:** Python 3.6+

```bash
# If Python is installed, this works immediately
sudo ./vijenex-cis
```

**Install Python if needed:**
```bash
sudo yum install python3
```

### Option 2: Go Binary (Recommended for Production)

**Requirements:** None (standalone binary)

**Build once:**
```bash
cd go-scanner
./build.sh
cd ..
```

**Then use:**
```bash
sudo ./vijenex-cis
# Select option 2
```

**Benefits:**
- No Python dependency
- Single 10MB binary
- Runs on any RHEL 8 system
- Fastest performance

### Option 3: Shell Script (Coming Soon)

**Requirements:** None (pure Bash)

Pure shell script implementation for maximum compatibility.

## Usage Examples

```bash
# Basic scan (auto-selects scanner)
sudo ./vijenex-cis

# Custom output directory
sudo ./vijenex-cis --output-dir /var/log/security

# Level 2 profile
sudo ./vijenex-cis --profile Level2

# Specific milestones
sudo ./vijenex-cis --milestones milestone-1-1.json milestone-2-1.json

# CSV format only
sudo ./vijenex-cis --format csv

# Help
./vijenex-cis --help
```

## Current Status

✅ **77 Controls Implemented** across 7 milestones:
- Section 1: Filesystem, Package Management, Secure Boot, SELinux (58 controls)
- Section 2: Time Synchronization, Special Purpose Services (19 controls)

## Output

### Reports Generated
- `vijenex-cis-results.csv` - 7-column CSV format
- `vijenex-cis-report.html` - HTML report with summary

### CSV Format
```
Id,Title,Section,Status,CISReference,Remediation,Description
1.1.1.1,Ensure cramfs kernel module is not available,1.1 Filesystem,PASS,...
```

## Production Deployment

### Scenario 1: Server Has Python
```bash
git clone https://github.com/vijenex/linux-cis-scanner.git
cd linux-cis-scanner/rhel-8
sudo ./vijenex-cis
# Auto-uses Python scanner
```

### Scenario 2: Server Has No Python
```bash
# On dev machine with Go:
cd rhel-8/go-scanner
./build.sh

# Copy binary to production:
scp bin/vijenex-cis user@prod-server:/usr/local/bin/

# On production:
sudo /usr/local/bin/vijenex-cis --output-dir /tmp/scan-results
```

### Scenario 3: No Dependencies Available
```bash
# Use shell script (coming soon)
sudo ./vijenex-cis
# Select option 3
```

## Architecture

```
rhel-8/
├── vijenex-cis              # Smart launcher (detects & selects)
├── scripts/
│   └── vijenex-cis.py       # Python scanner
├── go-scanner/
│   ├── bin/vijenex-cis      # Go binary (after build)
│   └── build.sh             # Build script
├── shell-scanner/           # Coming soon
├── milestones/
│   ├── milestone-1-1.json   # 15 controls
│   ├── milestone-1-2.json   # 22 controls
│   ├── milestone-1-3.json   # 6 controls
│   ├── milestone-1-4.json   # 7 controls
│   ├── milestone-1-5.json   # 8 controls
│   ├── milestone-2-1.json   # 4 controls
│   └── milestone-2-2.json   # 15 controls
└── README.md
```

## Comparison

| Feature | Python | Go Binary | Shell Script |
|---------|--------|-----------|--------------|
| **Dependencies** | Python 3.6+ | None | None |
| **Build Required** | No | Yes (once) | No |
| **Speed** | Fast | Fastest | Slower |
| **Size** | ~100KB | ~10MB | ~50KB |
| **Portability** | Needs Python | Runs anywhere | Runs anywhere |
| **Best For** | Dev/Test | Production | Legacy systems |

## Troubleshooting

### No scanner available
```bash
# Install Python
sudo yum install python3

# Or build Go binary
cd go-scanner && ./build.sh
```

### Permission denied
```bash
# Run with sudo
sudo ./vijenex-cis
```

### Python not found
```bash
# Install Python 3
sudo yum install python3
```

### Go binary not built
```bash
# Build it
cd go-scanner
./build.sh
```

## Next Steps

1. **Test now:** Use Python scanner (if Python installed)
2. **Build Go binary:** For production deployment
3. **Wait for shell script:** For maximum compatibility

## Support

- GitHub: https://github.com/vijenex/linux-cis-scanner
- Email: support@vijenex.com
