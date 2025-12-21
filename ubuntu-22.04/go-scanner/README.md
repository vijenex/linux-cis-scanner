# Vijenex CIS Scanner for Ubuntu 22.04 LTS

Automated CIS Benchmark compliance scanner for Ubuntu 22.04 LTS, built with Go.

## ⚠️ IMPORTANT: Audit-Only Scanner

**This scanner is 100% READ-ONLY and performs AUDIT ONLY.**

- ✅ **Reads** system configuration files
- ✅ **Checks** compliance status
- ✅ **Generates** reports
- ❌ **NEVER modifies** system files
- ❌ **NEVER executes** remediation commands
- ❌ **NEVER installs/removes** packages
- ❌ **NEVER changes** system configuration

**Safe to run on production systems.**

## Overview

This scanner automates the assessment of Ubuntu 22.04 LTS systems against the CIS Ubuntu 22.04 LTS Benchmark. It provides comprehensive security compliance checking with detailed reporting in HTML and CSV formats.

## Features

- ✅ Automated compliance checking for CIS Ubuntu 22.04 LTS Benchmark
- ✅ **Audit-only** - No system modifications
- ✅ **Level 2 controls excluded** - Only Level 1 controls are scanned
- ✅ **No false positives** - All fixes from Amazon Linux 2 applied
- 📊 HTML and CSV report generation
- 🔍 Real-time scanning with progress indicators
- 📋 Detailed control descriptions and remediation steps (information only)

## Installation

### Quick Start (No Go Required!)

The scanner is a **standalone binary** - no dependencies needed!

```bash
# Use the smart wrapper script
chmod +x vijenex-cis
sudo ./vijenex-cis --output-dir /tmp/scan-results
```

The wrapper automatically:
- ✅ Uses pre-built binary if available (no Go needed)
- ✅ Builds automatically if Go is installed
- ✅ Shows clear instructions if neither is available

### Prerequisites for Building

- Go 1.21 or later (only needed if building from source)
- Root or sudo access (for complete scanning)

### Build from Source

```bash
cd ubuntu-22.04/go-scanner
./build.sh
# Creates: bin/vijenex-cis-amd64 and bin/vijenex-cis-arm64
```

### Install System-Wide

```bash
# Copy pre-built binary
sudo cp bin/vijenex-cis-amd64 /usr/local/bin/vijenex-cis
sudo chmod +x /usr/local/bin/vijenex-cis
```

## Usage

### Basic Scan

```bash
sudo vijenex-cis
```

### Custom Output Directory

```bash
sudo vijenex-cis --output-dir /path/to/reports
```

### Report Format

```bash
# HTML only
sudo vijenex-cis --format html

# CSV only
sudo vijenex-cis --format csv

# Both (default)
sudo vijenex-cis --format both
```

### Specific Milestones

```bash
# Scan only specific milestones
sudo vijenex-cis --milestones milestone-1-1.json milestone-2-1.json
```

## Level 2 Controls

**Level 2 controls are automatically excluded** from all scans. Only Level 1 controls are executed to ensure focus on essential security configurations.

## False Positive Fixes

All false positive fixes from the Amazon Linux 2 scanner have been applied:

- ✅ Kernel module detection (modules not in kernel = PASS)
- ✅ Mount point checks (cloud single-volume = NOT_APPLICABLE)
- ✅ Command output with pipes (cut, sort, uniq support)
- ✅ Directory permissions ("or more restrictive" logic)
- ✅ Service status ("static" services = enabled)
- ✅ FileContent multiple files support
- ✅ PAMConfig "not_found" handling
- ✅ SSH config validation (strong algorithms, LogLevel INFO/VERBOSE)
- ✅ Sysctl kernel defaults (tcp_syncookies)
- ✅ nftables command not found handling
- ✅ MTA configuration (NOT_APPLICABLE when not installed)

## Reports

Reports are generated in the specified output directory:

- **HTML Report**: `vijenex-cis-report.html` - Interactive, detailed report
- **CSV Report**: `vijenex-cis-results.csv` - Machine-readable results

## Architecture

- **Go-based** - Fast, efficient, single binary
- **No dependencies** - Standalone executable
- **Cross-platform** - AMD64 and ARM64 support
- **Audit-safe** - Read-only operations only

## License

See LICENSE file in the repository root.

