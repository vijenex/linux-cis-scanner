# CentOS 7 Scanner - Quick Start

## Simple Usage

After cloning the repository:

```bash
cd centos-7/go-scanner
sudo ./scan.sh
```

That's it! The script will:
- Auto-detect your architecture (x86_64 or aarch64)
- Build the scanner if needed
- Run the scan
- Generate reports in `./reports/` directory

## Options

```bash
# Custom output directory
sudo ./scan.sh /tmp/my-results

# With additional scanner options
sudo ./scan.sh ./reports --format html
sudo ./scan.sh ./reports --profile Level1
```

## Reports

After scanning, check:
- `./reports/vijenex-cis-results-<IP>.csv` - CSV report
- `./reports/vijenex-cis-report-<IP>.html` - HTML report

## Requirements

- CentOS 7 system
- Root access (for some checks)
- Go installed (if binary needs to be built)

The script will automatically build the binary if it doesn't exist.

