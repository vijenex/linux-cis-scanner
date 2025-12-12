# Vijenex CIS Scanner - Package Building Guide

This directory contains packaging files for creating installable RPM and DEB packages, similar to OpenSCAP.

## Package Types

### RPM Package (RHEL/CentOS/Fedora)
- **File**: `vijenex-cis-scanner-1.0.0-1.rpm`
- **Supported**: RHEL 8, RHEL 9, CentOS 7
- **Install Location**: `/usr/share/vijenex-cis/`
- **Binary**: `/usr/bin/vijenex-cis`

### DEB Package (Ubuntu/Debian)
- **File**: `vijenex-cis-scanner_1.0.0_all.deb`
- **Supported**: Ubuntu 20.04, 22.04, 24.04, Debian 11
- **Install Location**: `/usr/share/vijenex-cis/`
- **Binary**: `/usr/bin/vijenex-cis`

## Building Packages

### Build RPM (on RHEL/CentOS)

```bash
# Install build tools
sudo yum install rpm-build

# Build package
cd /path/to/Linux-CIS-Audit-code
./packaging/build-rpm.sh

# Output: packaging/rpm/dist/vijenex-cis-scanner-1.0.0-1.*.rpm
```

### Build DEB (on Ubuntu/Debian)

```bash
# Install build tools
sudo apt install dpkg-dev

# Build package
cd /path/to/Linux-CIS-Audit-code
./packaging/build-deb.sh

# Output: packaging/deb/dist/vijenex-cis-scanner_1.0.0_all.deb
```

## Installing Packages

### Install RPM

```bash
# Method 1: Using rpm
sudo rpm -ivh vijenex-cis-scanner-1.0.0-1.*.rpm

# Method 2: Using yum (handles dependencies)
sudo yum localinstall vijenex-cis-scanner-1.0.0-1.*.rpm

# Method 3: Using dnf (RHEL 8+)
sudo dnf install vijenex-cis-scanner-1.0.0-1.*.rpm
```

### Install DEB

```bash
# Method 1: Using dpkg
sudo dpkg -i vijenex-cis-scanner_1.0.0_all.deb
sudo apt-get install -f  # Fix dependencies if needed

# Method 2: Using apt (handles dependencies)
sudo apt install ./vijenex-cis-scanner_1.0.0_all.deb
```

## Using Installed Scanner

After installation, the scanner works exactly like OpenSCAP:

```bash
# Complete scan
sudo vijenex-cis

# Level 2 scan
sudo vijenex-cis --profile Level2

# Custom output directory
sudo vijenex-cis --output-dir /tmp/security-reports

# CSV format only
sudo vijenex-cis --format csv

# Specific milestones
sudo vijenex-cis --milestones milestone-1-1.json milestone-1-2.json

# View manual
man vijenex-cis

# Get help
vijenex-cis --help
```

## Default Locations

### Installed Files
- **Binary**: `/usr/bin/vijenex-cis`
- **Scanners**: `/usr/share/vijenex-cis/{rhel-8,rhel-9,ubuntu-22.04,...}/`
- **Config**: `/etc/vijenex-cis/`
- **Reports**: `/var/log/vijenex-cis/{os}-{version}-reports/`
- **Man Page**: `/usr/share/man/man1/vijenex-cis.1`

### Report Output
- **Default**: `/var/log/vijenex-cis/rhel-8-reports/` (or ubuntu-22.04-reports, etc.)
- **Custom**: Use `--output-dir` flag

## Uninstalling

### Remove RPM
```bash
sudo rpm -e vijenex-cis-scanner
# or
sudo yum remove vijenex-cis-scanner
```

### Remove DEB
```bash
sudo dpkg -r vijenex-cis-scanner
# or
sudo apt remove vijenex-cis-scanner
```

## Package Contents

### RPM Package Structure
```
/usr/bin/vijenex-cis                    # Wrapper script
/usr/share/vijenex-cis/
├── rhel-8/                             # RHEL 8 scanner
│   ├── scripts/vijenex-cis.py
│   └── milestones/*.json
├── rhel-9/                             # RHEL 9 scanner
├── centos-7/                           # CentOS 7 scanner
├── LICENSE
└── README.md
/etc/vijenex-cis/                       # Config directory
/var/log/vijenex-cis/                   # Reports directory
/usr/share/man/man1/vijenex-cis.1       # Man page
```

### DEB Package Structure
```
/usr/bin/vijenex-cis                    # Wrapper script
/usr/share/vijenex-cis/
├── ubuntu-20.04/                       # Ubuntu 20.04 scanner
├── ubuntu-22.04/                       # Ubuntu 22.04 scanner
├── ubuntu-24.04/                       # Ubuntu 24.04 scanner
├── debian-11/                          # Debian 11 scanner
├── LICENSE
└── README.md
/etc/vijenex-cis/                       # Config directory
/var/log/vijenex-cis/                   # Reports directory
/usr/share/man/man1/vijenex-cis.1.gz    # Man page (compressed)
```

## Comparison with OpenSCAP

| Feature | OpenSCAP | Vijenex CIS |
|---------|----------|-------------|
| Installation | `yum install openscap-scanner` | `yum install vijenex-cis-scanner` |
| Command | `oscap xccdf eval ...` | `vijenex-cis --profile Level1` |
| Reports | XML/HTML | HTML/CSV |
| Content | `/usr/share/xml/scap/` | `/usr/share/vijenex-cis/` |
| Man Page | `man oscap` | `man vijenex-cis` |
| Root Required | Yes | Yes |

## Dependencies

### RPM Package
- `python3 >= 3.6`

### DEB Package
- `python3 >= 3.6`

## Version Information

- **Version**: 1.0.0
- **Release**: 1
- **Architecture**: noarch (all)
- **License**: MIT

## Support

For issues or questions:
- GitHub: https://github.com/vijenex/linux-cis-scanner
- Email: support@vijenex.com
