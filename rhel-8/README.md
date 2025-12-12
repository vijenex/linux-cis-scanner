# Vijenex CIS Scanner for RHEL 8

CIS Red Hat Enterprise Linux 8 Benchmark v4.0.0 Compliance Scanner

## Features

- ✅ Automated CIS compliance scanning
- ✅ 350+ security controls
- ✅ CSV and HTML report generation
- ✅ Color-coded terminal output
- ✅ Milestone-based architecture
- ✅ No false positives (command-based checks)

## Requirements

- Red Hat Enterprise Linux 8.x
- Python 3.6+
- Root/sudo access

## Installation

```bash
cd /Users/satish.korra/Desktop/Linux-CIS-Audit-code/rhel-8/scripts
chmod +x vijenex-cis.py
```

## Usage

### Direct Python Execution
```bash
# Navigate to RHEL 8 scripts directory
cd /path/to/rhel-8/scripts

# Complete compliance scan
sudo python3 vijenex-cis.py

# Level 2 profile scan
sudo python3 vijenex-cis.py --profile Level2

# Custom output directory
sudo python3 vijenex-cis.py --output-dir /tmp/my-reports

# Generate specific report formats
sudo python3 vijenex-cis.py --format html
sudo python3 vijenex-cis.py --format csv

# Run specific milestones
sudo python3 vijenex-cis.py --milestones milestone-1-1.json milestone-1-2.json
```

### Parameters

| Parameter | Description | Default | Example |
|-----------|-------------|---------|---------|
| `--output-dir` | Report output directory | `../reports` | `--output-dir /var/log/audit` |
| `--profile` | CIS profile level | `Level1` | `--profile Level2` |
| `--format` | Report format | `both` | `--format html` or `--format csv` |
| `--milestones` | Specific milestone files | All files | `--milestones milestone-1-1.json` |

## Output

Reports are generated in `../reports/` directory:
- `vijenex-cis-results.csv` - Detailed CSV report
- `vijenex-cis-report.html` - HTML report with charts

### CLI Output
- **Green ✓**: PASSED controls
- **Red ✗**: FAILED controls
- **Yellow ⚠**: MANUAL verification required
- **Cyan ?**: SKIPPED controls

## CSV Format (7 Columns)

| Id | Title | Section | Status | CISReference | Remediation | Description |
|----|-------|---------|--------|--------------|-------------|-------------|
| 1.1.1.1 | Control Title | Section | PASS/FAIL/MANUAL | Level info | Steps | Details |

## Implementation Status

### ✅ Completed Milestones (59 controls)
- **Milestone 1.1**: Filesystem - Kernel Modules & /tmp (16 controls)
- **Milestone 1.2**: Filesystem - /dev/shm, /home, /var partitions (22 controls)
- **Milestone 1.3**: Package Management & AIDE (6 controls)
- **Milestone 1.4**: Secure Boot & Process Hardening (7 controls)
- **Milestone 1.5**: SELinux Configuration (8 controls)

### 🚧 Next Milestones
- Milestone 2.1: Services - Special Purpose Services
- Milestone 2.2: Services - Client Services
- Milestone 3.x: Network Configuration
- Milestone 4.x: Logging and Auditing
- Milestone 5.x: Access Control
- Milestone 6.x: System Maintenance

**Scanner is ready to test on RHEL 8 systems!**

## Support

For issues or questions:
- GitHub: https://github.com/vijenex/linux-cis-scanner
- Email: support@vijenex.com

## License

© 2024 Vijenex Security Platform
