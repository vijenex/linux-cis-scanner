# Vijenex CIS Scanner for Amazon Linux 2

Automated CIS Benchmark compliance scanner for Amazon Linux 2, built with Go.

## Overview

This scanner automates the assessment of Amazon Linux 2 systems against the CIS Amazon Linux 2 Benchmark. It provides comprehensive security compliance checking with detailed reporting in HTML and CSV formats.

## Features

- ✅ Automated compliance checking for CIS Amazon Linux 2 Benchmark
- 📊 HTML and CSV report generation
- 🔍 Real-time scanning with progress indicators
- 🎯 Profile-based scanning (Level 1, Level 2)
- 📋 Detailed control descriptions and remediation steps

## Installation

### Prerequisites

- Go 1.21 or later
- Root or sudo access (for complete scanning)

### Build from Source

```bash
cd amazon-linux-2/go-scanner
make deps
make build
```

### Install System-Wide

```bash
make install
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

### Profile Selection

```bash
# Level 1 profile (default)
sudo vijenex-cis --profile Level1

# Level 2 profile
sudo vijenex-cis --profile Level2
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
sudo vijenex-cis --milestones milestone-1-1.json milestone-1-2.json
```

## Control Types

The scanner supports the following automated control types:

- **KernelModule**: Check kernel module availability
- **MountPoint**: Verify separate partition existence
- **MountOption**: Check mount options (nodev, nosuid, noexec)
- **ServiceStatus**: Verify service enabled/disabled status
- **PackageInstalled**: Check package installation status
- **PackageNotInstalled**: Verify package removal
- **SysctlParameter**: Check sysctl parameter values
- **FilePermissions**: Verify file permissions, owner, and group
- **FileContent**: Check file content patterns
- **SSHConfig**: Verify SSH configuration parameters
- **PAMConfig**: Check PAM module configuration
- **SudoConfig**: Verify sudo configuration
- **CommandOutputEmpty**: Check command output is empty
- **FileExists**: Verify file existence

## Milestone Files

Milestone files are JSON documents that define groups of controls. They are located in the `milestones/` directory.

### Milestone Structure

```json
{
  "milestone": "1.1",
  "version": "1.0.0",
  "description": "Section description",
  "section": "1 Initial Setup",
  "controls": [
    {
      "id": "1.1.1.1",
      "title": "Control title",
      "section": "1.1.1 Filesystem Kernel Modules",
      "profile": "Level1",
      "automated": true,
      "type": "KernelModule",
      "module_name": "cramfs",
      "expected_status": "not_available",
      "cis_reference": "CIS Amazon Linux 2 - 1.1.1.1",
      "description": "Control description",
      "remediation": "Remediation steps"
    }
  ]
}
```

## Report Output

### HTML Report

The HTML report provides an interactive view of compliance results with:
- Summary metrics (Passed, Failed, Manual)
- Detailed control results
- Expandable control details
- CIS references and remediation steps

### CSV Report

The CSV report provides machine-readable output with:
- Control ID
- Title
- Section
- Status
- CIS Reference
- Remediation
- Description

## Development

### Project Structure

```
amazon-linux-2/go-scanner/
├── cmd/
│   └── main.go              # Main entry point
├── internal/
│   ├── controls/            # Control check implementations
│   ├── scanner/             # Scanner logic
│   └── report/              # Report generation
├── milestones/              # Control milestone files
├── bin/                     # Build output
└── Makefile                 # Build automation
```

### Adding New Controls

1. Create or update milestone JSON files in `milestones/`
2. Ensure control types match supported types
3. Test with: `go run ./cmd --milestones milestone-X.json`

### Building

```bash
# Build for current platform
make build

# Build for Linux AMD64
make build-linux

# Build for all platforms
make build-all
```

## Status Values

- **PASS**: Control check passed
- **FAIL**: Control check failed
- **MANUAL**: Manual verification required
- **NOT_APPLICABLE**: Control not applicable to current configuration
- **ERROR**: Error during control execution

## Contributing

When adding new controls or milestones:

1. Follow the existing JSON structure
2. Use appropriate control types
3. Include comprehensive descriptions and remediation steps
4. Test thoroughly before submitting

## References

- [CIS Amazon Linux 2 Benchmark](https://www.cisecurity.org/benchmark/amazon_linux)
- [Vijenex Security Platform](https://github.com/vijenex/linux-cis-scanner)

## License

See LICENSE file in the root directory.

