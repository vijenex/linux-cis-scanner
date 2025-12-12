# Vijenex CIS Scanner - Package Architecture

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    USER INSTALLS PACKAGE                     │
│                                                              │
│  RHEL/CentOS: sudo yum install vijenex-cis-scanner.rpm     │
│  Ubuntu/Debian: sudo apt install vijenex-cis-scanner.deb   │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│              FILES INSTALLED TO SYSTEM                       │
│                                                              │
│  /usr/bin/vijenex-cis          ← Wrapper script (in PATH)  │
│  /usr/share/vijenex-cis/       ← Scanner files              │
│  /etc/vijenex-cis/             ← Configuration              │
│  /var/log/vijenex-cis/         ← Reports directory          │
│  /usr/share/man/man1/          ← Man page                   │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                  USER RUNS COMMAND                           │
│                                                              │
│              $ sudo vijenex-cis --profile Level1            │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│              WRAPPER SCRIPT EXECUTES                         │
│                                                              │
│  1. Detect OS: Read /etc/os-release                         │
│  2. Determine scanner directory:                            │
│     - RHEL 8 → /usr/share/vijenex-cis/rhel-8/              │
│     - Ubuntu 22.04 → /usr/share/vijenex-cis/ubuntu-22.04/  │
│  3. Set output directory:                                   │
│     - Default: /var/log/vijenex-cis/{os}-{version}/        │
│     - Custom: User-specified via --output-dir               │
│  4. Execute: python3 scripts/vijenex-cis.py                 │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│              PYTHON SCANNER EXECUTES                         │
│                                                              │
│  1. Load milestone JSON files                               │
│  2. Execute CIS controls                                    │
│  3. Generate reports (HTML/CSV)                             │
│  4. Save to output directory                                │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                  REPORTS GENERATED                           │
│                                                              │
│  /var/log/vijenex-cis/rhel-8-reports/                      │
│  ├── vijenex-cis-report.html                               │
│  └── vijenex-cis-results.csv                               │
└─────────────────────────────────────────────────────────────┘
```

## Directory Structure After Installation

```
/usr/
├── bin/
│   └── vijenex-cis                     # Main command (wrapper)
└── share/
    ├── vijenex-cis/                    # Scanner installation
    │   ├── rhel-8/                     # RHEL 8 scanner
    │   │   ├── scripts/
    │   │   │   └── vijenex-cis.py      # Python scanner
    │   │   └── milestones/
    │   │       ├── milestone-1-1.json
    │   │       ├── milestone-1-2.json
    │   │       └── ...
    │   ├── rhel-9/                     # RHEL 9 scanner
    │   ├── ubuntu-22.04/               # Ubuntu 22.04 scanner
    │   ├── ubuntu-24.04/               # Ubuntu 24.04 scanner
    │   ├── LICENSE
    │   └── README.md
    └── man/
        └── man1/
            └── vijenex-cis.1.gz        # Man page

/etc/
└── vijenex-cis/                        # Configuration directory
    └── (future config files)

/var/
└── log/
    └── vijenex-cis/                    # Reports directory
        ├── rhel-8-reports/
        ├── rhel-9-reports/
        ├── ubuntu-22.04-reports/
        └── ubuntu-24.04-reports/
```

## Package Build Process

### RPM Build Flow

```
Source Files
    ↓
packaging/build-rpm.sh
    ↓
Create tarball → ~/rpmbuild/SOURCES/
    ↓
Copy spec file → ~/rpmbuild/SPECS/
    ↓
rpmbuild -ba vijenex-cis-scanner.spec
    ↓
Build RPM → ~/rpmbuild/RPMS/noarch/
    ↓
Copy to packaging/rpm/dist/
    ↓
vijenex-cis-scanner-1.0.0-1.el8.noarch.rpm
```

### DEB Build Flow

```
Source Files
    ↓
packaging/build-deb.sh
    ↓
Create build directory structure
    ↓
Copy files to build/usr/share/vijenex-cis/
    ↓
Copy wrapper to build/usr/bin/
    ↓
Create DEBIAN control files
    ↓
dpkg-deb --build
    ↓
Copy to packaging/deb/dist/
    ↓
vijenex-cis-scanner_1.0.0_all.deb
```

## OS Detection Logic

```
User runs: vijenex-cis
    ↓
Wrapper reads: /etc/os-release
    ↓
┌─────────────────────────────────────┐
│ Extract: ID and VERSION_ID          │
│                                     │
│ ID=rhel, VERSION_ID=8.5             │
│ ID=ubuntu, VERSION_ID=22.04         │
│ ID=centos, VERSION_ID=7             │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│ Determine Scanner Directory         │
│                                     │
│ RHEL 8.x → rhel-8/                  │
│ RHEL 9.x → rhel-9/                  │
│ Ubuntu 22.04 → ubuntu-22.04/        │
│ Ubuntu 24.04 → ubuntu-24.04/        │
│ CentOS 7 → centos-7/                │
└─────────────────────────────────────┘
    ↓
Execute: python3 /usr/share/vijenex-cis/{scanner}/scripts/vijenex-cis.py
```

## Command Flow

```
$ sudo vijenex-cis --profile Level2 --output-dir /tmp/reports
    ↓
/usr/bin/vijenex-cis (wrapper script)
    ↓
Detect OS: RHEL 8
    ↓
Set SCANNER_DIR=/usr/share/vijenex-cis/rhel-8
    ↓
Check for --output-dir flag: YES → Use /tmp/reports
    ↓
cd /usr/share/vijenex-cis/rhel-8
    ↓
exec python3 scripts/vijenex-cis.py --output-dir /tmp/reports --profile Level2
    ↓
Python scanner loads milestones from ./milestones/
    ↓
Execute CIS controls
    ↓
Generate reports in /tmp/reports/
    ↓
Exit with status code
```

## Comparison: Git Clone vs Package Install

### Git Clone Method (Old)

```
User's Machine
└── /home/user/projects/
    └── linux-cis-scanner/          ← Git clone
        ├── rhel-8/
        │   ├── scripts/
        │   │   └── vijenex-cis.py
        │   └── milestones/
        └── ubuntu-22.04/

Command: cd rhel-8 && python3 scripts/vijenex-cis.py
```

### Package Install Method (New)

```
System Directories
├── /usr/bin/
│   └── vijenex-cis                 ← In PATH
└── /usr/share/vijenex-cis/
    ├── rhel-8/
    │   ├── scripts/
    │   │   └── vijenex-cis.py
    │   └── milestones/
    └── ubuntu-22.04/

Command: vijenex-cis (from anywhere)
```

## Package Contents

### RPM Package Contents

```
vijenex-cis-scanner-1.0.0-1.el8.noarch.rpm
├── /usr/bin/vijenex-cis
├── /usr/share/vijenex-cis/
│   ├── rhel-8/
│   ├── rhel-9/
│   ├── centos-7/
│   ├── LICENSE
│   └── README.md
├── /etc/vijenex-cis/
├── /var/log/vijenex-cis/
└── /usr/share/man/man1/vijenex-cis.1.gz

Metadata:
- Name: vijenex-cis-scanner
- Version: 1.0.0
- Release: 1
- Requires: python3 >= 3.6
- Architecture: noarch
```

### DEB Package Contents

```
vijenex-cis-scanner_1.0.0_all.deb
├── /usr/bin/vijenex-cis
├── /usr/share/vijenex-cis/
│   ├── ubuntu-20.04/
│   ├── ubuntu-22.04/
│   ├── ubuntu-24.04/
│   ├── debian-11/
│   ├── LICENSE
│   └── README.md
├── /etc/vijenex-cis/
├── /var/log/vijenex-cis/
└── /usr/share/man/man1/vijenex-cis.1.gz

Metadata:
- Package: vijenex-cis-scanner
- Version: 1.0.0
- Depends: python3 >= 3.6
- Architecture: all
```

## Installation vs Uninstallation

### Installation

```
Package Manager (yum/apt)
    ↓
Extract package contents
    ↓
Copy files to system directories
    ↓
Set permissions (755 for binaries)
    ↓
Run post-install script
    ↓
Update man database
    ↓
Display success message
```

### Uninstallation

```
Package Manager (yum/apt)
    ↓
Remove files from system directories
    ↓
Remove /usr/bin/vijenex-cis
    ↓
Remove /usr/share/vijenex-cis/
    ↓
Keep /etc/vijenex-cis/ (config)
    ↓
Keep /var/log/vijenex-cis/ (reports)
    ↓
Update man database
```

## Security Considerations

```
File Permissions:
├── /usr/bin/vijenex-cis           → 755 (rwxr-xr-x)
├── /usr/share/vijenex-cis/        → 755 (rwxr-xr-x)
├── /etc/vijenex-cis/              → 755 (rwxr-xr-x)
└── /var/log/vijenex-cis/          → 755 (rwxr-xr-x)

Ownership:
└── root:root (all files)

Execution:
└── Requires sudo for system scanning
```

## Summary

This architecture provides:

✅ **Professional installation** like OpenSCAP
✅ **System-wide availability** (in PATH)
✅ **Automatic OS detection** (no manual config)
✅ **Clean separation** (code vs data vs config)
✅ **Standard compliance** (FHS compliant)
✅ **Easy updates** (via package manager)
✅ **Clean uninstall** (complete removal)
