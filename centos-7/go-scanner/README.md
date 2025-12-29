# Vijenex CIS Scanner for CentOS 7

CIS Benchmark v3.1.2 compliance scanner for CentOS Linux 7.

## Features

- ✅ **No False Positives**: All lessons learned from RHEL 8/9 applied
- ✅ **Level 1 Only**: Level 2 controls excluded from milestones
- ✅ **Complete Context**: Full ScanContext implementation with all builders
- ✅ **Proper Mount Handling**: Returns NOT_APPLICABLE when partitions don't exist
- ✅ **Context Caching**: Efficient package/service/kernel module checks

## Building

```bash
cd centos-7/go-scanner
./build.sh
```

This will create binaries for:
- `bin/vijenex-cis-amd64` (x86_64)
- `bin/vijenex-cis-arm64` (aarch64)

## Installation

Copy the appropriate binary to your CentOS 7 server:

```bash
# For x86_64
scp bin/vijenex-cis-amd64 user@server:/usr/local/bin/vijenex-cis
chmod +x /usr/local/bin/vijenex-cis

# For aarch64
scp bin/vijenex-cis-arm64 user@server:/usr/local/bin/vijenex-cis
chmod +x /usr/local/bin/vijenex-cis
```

## Usage

Run the scanner (requires root for some checks):

```bash
sudo vijenex-cis --output-dir /tmp/scan-results
```

Options:
- `--output-dir`: Directory for reports (default: `./reports`)
- `--profile`: CIS profile level (default: `Level1`)
- `--format`: Report format - `html`, `csv`, or `both` (default: `both`)
- `--milestones`: Specific milestone files to scan (default: all)

## Reports

The scanner generates:
- **CSV Report**: `vijenex-cis-results-<IP>.csv`
- **HTML Report**: `vijenex-cis-report-<IP>.html`

## Important Notes

1. **Level 2 Controls Excluded**: All Level 2 controls are excluded from milestone JSON files
2. **Unsupported Controls Excluded**: Controls that don't apply to CentOS 7 are excluded
3. **False Positive Fixes Applied**:
   - Mount options return NOT_APPLICABLE when partition doesn't exist
   - Proper context caching for packages/services
   - Complete ScanContext with all builders
   - Proper error handling

## Milestone Files

Milestone JSON files should be generated from the official CIS PDF:
`CIS_CentOS_Linux_7_Benchmark_v3.1.2.pdf`

The milestone files should:
- Include only Level 1 controls
- Exclude unsupported controls
- Use official ID, title, description, and remediation from the PDF

## Development

```bash
# Install dependencies
go mod download

# Build
go build -o bin/vijenex-cis ./cmd

# Run tests (if available)
go test ./...
```

## License

See LICENSE file in repository root.

