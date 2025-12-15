# Vijenex CIS Scanner - RHEL 9

CIS Benchmark compliance scanner for Red Hat Enterprise Linux 9.

## Build

```bash
./build.sh
# or
make build
```

## Run

```bash
sudo ./bin/vijenex-cis --profile Level1 --format both --output-dir ./reports
```

## Options

- `--profile`: Level1 or Level2 (default: Level1)
- `--format`: html, csv, or both (default: both)
- `--output-dir`: Output directory for reports (default: ./reports)
- `--milestones`: Specific milestone files to scan

## CIS Benchmark

Based on CIS Red Hat Enterprise Linux 9 Benchmark v2.0.0
