# Package Testing Guide

## Test RPM Package (RHEL/CentOS)

### 1. Build Package
```bash
cd /path/to/Linux-CIS-Audit-code
./packaging/build-rpm.sh
```

### 2. Install Package
```bash
sudo yum localinstall packaging/rpm/dist/vijenex-cis-scanner-1.0.0-1.*.rpm
```

### 3. Verify Installation
```bash
# Check binary exists
which vijenex-cis
# Expected: /usr/bin/vijenex-cis

# Check files installed
ls /usr/share/vijenex-cis/
# Expected: rhel-8/ rhel-9/ centos-7/ LICENSE README.md

# Check man page
man vijenex-cis
# Expected: Man page displays

# Check version
vijenex-cis --help
# Expected: Help message displays
```

### 4. Test Scanner
```bash
# Test basic scan
sudo vijenex-cis --help

# Test Level 1 scan (quick test with 1 milestone)
sudo vijenex-cis --milestones milestone-1-1.json --output-dir /tmp/test-reports

# Check reports generated
ls /tmp/test-reports/
# Expected: vijenex-cis-report.html, vijenex-cis-results.csv

# Test full scan
sudo vijenex-cis --profile Level1 --output-dir /tmp/full-scan

# Check default output location
ls /var/log/vijenex-cis/
# Expected: rhel-8-reports/ or rhel-9-reports/
```

### 5. Test Uninstall
```bash
sudo yum remove vijenex-cis-scanner

# Verify removal
which vijenex-cis
# Expected: command not found

ls /usr/share/vijenex-cis/
# Expected: directory not found
```

## Test DEB Package (Ubuntu/Debian)

### 1. Build Package
```bash
cd /path/to/Linux-CIS-Audit-code
./packaging/build-deb.sh
```

### 2. Install Package
```bash
sudo apt install ./packaging/deb/dist/vijenex-cis-scanner_1.0.0_all.deb
```

### 3. Verify Installation
```bash
# Check binary exists
which vijenex-cis
# Expected: /usr/bin/vijenex-cis

# Check files installed
ls /usr/share/vijenex-cis/
# Expected: ubuntu-20.04/ ubuntu-22.04/ ubuntu-24.04/ debian-11/ LICENSE README.md

# Check man page
man vijenex-cis
# Expected: Man page displays

# Check version
vijenex-cis --help
# Expected: Help message displays
```

### 4. Test Scanner
```bash
# Test basic scan
sudo vijenex-cis --help

# Test Level 1 scan (quick test with 1 milestone)
sudo vijenex-cis --milestones milestone-1-1.json --output-dir /tmp/test-reports

# Check reports generated
ls /tmp/test-reports/
# Expected: vijenex-cis-report.html, vijenex-cis-results.csv

# Test full scan
sudo vijenex-cis --profile Level1 --output-dir /tmp/full-scan

# Check default output location
ls /var/log/vijenex-cis/
# Expected: ubuntu-22.04-reports/ or ubuntu-24.04-reports/
```

### 5. Test Uninstall
```bash
sudo apt remove vijenex-cis-scanner

# Verify removal
which vijenex-cis
# Expected: command not found

ls /usr/share/vijenex-cis/
# Expected: directory not found
```

## Test OS Detection

### Test on Different RHEL Versions

```bash
# On RHEL 8
sudo vijenex-cis --help
# Should use /usr/share/vijenex-cis/rhel-8/

# On RHEL 9
sudo vijenex-cis --help
# Should use /usr/share/vijenex-cis/rhel-9/

# On CentOS 7
sudo vijenex-cis --help
# Should use /usr/share/vijenex-cis/centos-7/
```

### Test on Different Ubuntu Versions

```bash
# On Ubuntu 20.04
sudo vijenex-cis --help
# Should use /usr/share/vijenex-cis/ubuntu-20.04/

# On Ubuntu 22.04
sudo vijenex-cis --help
# Should use /usr/share/vijenex-cis/ubuntu-22.04/

# On Ubuntu 24.04
sudo vijenex-cis --help
# Should use /usr/share/vijenex-cis/ubuntu-24.04/
```

## Test All Command Options

```bash
# Profile selection
sudo vijenex-cis --profile Level1
sudo vijenex-cis --profile Level2

# Output directory
sudo vijenex-cis --output-dir /tmp/custom-reports

# Report format
sudo vijenex-cis --format html
sudo vijenex-cis --format csv
sudo vijenex-cis --format both

# Specific milestones
sudo vijenex-cis --milestones milestone-1-1.json
sudo vijenex-cis --milestones milestone-1-1.json milestone-1-2.json

# Combined options
sudo vijenex-cis --profile Level2 --output-dir /tmp/reports --format csv
```

## Expected Results

### ✅ Successful Installation
- Binary available in PATH: `/usr/bin/vijenex-cis`
- Files installed: `/usr/share/vijenex-cis/`
- Man page works: `man vijenex-cis`
- Help displays: `vijenex-cis --help`

### ✅ Successful Scan
- Scanner runs without errors
- Reports generated in output directory
- HTML report viewable in browser
- CSV report contains all controls
- Exit code 0

### ✅ Successful Uninstall
- Binary removed from PATH
- Files removed from `/usr/share/vijenex-cis/`
- Man page removed
- Config directory can remain (optional)

## Troubleshooting

### Package Won't Install

**RPM:**
```bash
# Check dependencies
rpm -qpR vijenex-cis-scanner-1.0.0-1.*.rpm

# Force install (not recommended)
sudo rpm -ivh --nodeps vijenex-cis-scanner-1.0.0-1.*.rpm
```

**DEB:**
```bash
# Check dependencies
dpkg-deb -I vijenex-cis-scanner_1.0.0_all.deb

# Fix dependencies
sudo apt-get install -f
```

### Scanner Won't Run

```bash
# Check Python version
python3 --version
# Required: Python 3.6+

# Check permissions
ls -l /usr/bin/vijenex-cis
# Should be: -rwxr-xr-x

# Run with debug
bash -x /usr/bin/vijenex-cis --help
```

### Reports Not Generated

```bash
# Check output directory permissions
ls -ld /var/log/vijenex-cis/

# Create manually if needed
sudo mkdir -p /var/log/vijenex-cis/
sudo chmod 755 /var/log/vijenex-cis/

# Use custom output directory
sudo vijenex-cis --output-dir /tmp/reports
```

## Checklist

### Pre-Build
- [ ] All scanner files present (rhel-8/, ubuntu-22.04/, etc.)
- [ ] LICENSE file exists
- [ ] README.md exists
- [ ] Build tools installed (rpm-build or dpkg-dev)

### Post-Build
- [ ] Package file created
- [ ] Package size reasonable (< 10MB)
- [ ] Package metadata correct (`rpm -qpi` or `dpkg-deb -I`)

### Post-Install
- [ ] Binary in PATH
- [ ] Files in /usr/share/vijenex-cis/
- [ ] Man page works
- [ ] Help command works
- [ ] Scanner runs successfully
- [ ] Reports generated
- [ ] OS detection works

### Post-Uninstall
- [ ] Binary removed
- [ ] Files removed
- [ ] Man page removed
- [ ] No errors during removal
