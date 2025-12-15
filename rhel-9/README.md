# RHEL 9 CIS Scanner

CIS Benchmark compliance scanner for Red Hat Enterprise Linux 9 based on CIS RHEL 9 Benchmark v2.0.0.

## Structure

```
rhel-9/
├── go-scanner/          # Go-based scanner (PRIMARY)
│   ├── cmd/            # Main application
│   ├── internal/       # Core scanner logic
│   ├── milestones/     # 297 CIS controls across 27 milestone files
│   └── bin/            # Compiled binaries
```

## Controls Summary

- **Total Controls**: 297
- **Milestone Files**: 27
- **CIS Benchmark**: v2.0.0
- **Profiles**: Level 1 and Level 2

## Build

```bash
cd go-scanner
./build.sh
```

## Run

```bash
sudo ./bin/vijenex-cis --profile Level1 --format both
```

## Output Formats

- CSV: Machine-readable format
- HTML: Human-readable with detailed remediation

## Level 2 Controls

Level 2 controls are marked with `"profile": "Level2"` in milestone files and will be:
- Skipped when running with `--profile Level1`
- Marked as "Not Applicable" or "Skipped" in reports
