# Ubuntu 22.04 LTS CIS Compliance Scanner

## Overview
Complete CIS (Center for Internet Security) compliance scanner for Ubuntu 22.04 LTS systems. This scanner implements comprehensive security controls across all major CIS benchmark sections.

## Coverage Summary

### ✅ Complete Implementation (7 Sections, 19 Milestones, 290+ Controls)

**Section 1: Initial Setup (4 milestones)**
- 1.1 Filesystem Configuration
- 1.2 Package Management  
- 1.3 Mandatory Access Controls (AppArmor)
- 1.4 Bootloader Configuration

**Section 2: Services (3 milestones)**
- 2.1 Server Services
- 2.2 Client Services
- 2.3 Service Clients

**Section 3: Network Configuration (2 milestones)**
- 3.1 Network Parameters (Host Only)
- 3.2 Network Parameters (Host and Router)

**Section 4: Host Based Firewall (1 milestone)**
- 4.1 Configure Host Based Firewall

**Section 5: Access Control (4 milestones)**
- 5.1 Configure SSH Server
- 5.2 Configure Privilege Escalation
- 5.3 Pluggable Authentication Modules (PAM)
- 5.4 User Accounts and Environment

**Section 6: Logging and Auditing (3 milestones)**
- 6.1 System Logging (journald, rsyslog, logfiles)
- 6.2 System Auditing (auditd, audit rules, log permissions)
- 6.3 Filesystem Integrity Checking (AIDE)

**Section 7: System Maintenance (2 milestones)**
- 7.1 System File Permissions
- 7.2 Local User and Group Settings

## Control Types Supported

- **FilePermission**: File/directory permissions and ownership
- **Service**: systemd service status checks
- **KernelParameter**: sysctl parameter validation
- **Package**: Package installation verification
- **ConfigFile**: Configuration file pattern matching
- **KernelModule**: Kernel module availability checks
- **MountOption**: Mount point option validation
- **AppArmorProfile**: AppArmor profile status
- **UFWStatus/UFWLoopback/UFWDefaultPolicy**: UFW firewall controls
- **SSHDConfig**: SSH daemon configuration
- **SudoConfig**: sudo configuration validation
- **PAMConfig**: PAM module configuration
- **JournaldConfig**: systemd-journald settings
- **RsyslogConfig**: rsyslog configuration
- **AuditdConfig**: auditd daemon configuration
- **AuditRule**: audit rule validation
- **LogFilePermissions**: Log file security
- **WorldWritableFiles**: World-writable file detection
- **OrphanedFiles**: Orphaned file detection
- **DuplicateUIDs/GIDs**: Duplicate ID detection
- **UserHomeDirs**: User home directory validation

## Quick Start

### Installation
```bash
# Install scanner system-wide
sudo bash /path/to/Linux-CIS-Audit-code/install.sh

# Or run directly
cd ubuntu-22.04
sudo python3 scripts/vijenex-cis.py
```

### Basic Usage

#### System-wide Installation (Recommended)
```bash
# Install scanner system-wide
sudo bash /path/to/Linux-CIS-Audit-code/install.sh

# Run complete Level 1 scan
sudo vijenex-cis --profile Level1

# Run specific milestones
sudo vijenex-cis --milestones milestone-1-1.json milestone-5-1.json

# Generate specific report format
sudo vijenex-cis --format html
sudo vijenex-cis --format csv
```

#### Direct Usage (without installation)
```bash
# Navigate to ubuntu-22.04 directory
cd ubuntu-22.04

# Run complete scan
sudo python3 scripts/vijenex-cis.py

# Run with specific options
sudo python3 scripts/vijenex-cis.py --profile Level1 --format both

# Run specific milestones
sudo python3 scripts/vijenex-cis.py --milestones milestone-1-1.json milestone-5-1.json

# Custom output directory
sudo python3 scripts/vijenex-cis.py --output-dir /custom/reports/
```

### Advanced Options
```bash
# Level 2 profile (more restrictive)
sudo python3 scripts/vijenex-cis.py --profile Level2

# Multiple specific milestones
sudo python3 scripts/vijenex-cis.py --milestones milestone-1-1.json milestone-2-1.json milestone-5-1.json

# All report formats
sudo python3 scripts/vijenex-cis.py --format both
```

## Report Formats

### HTML Report
- **Default Location**: `./linux-cis-report.html` (current directory)
- **Custom Location**: Use `--output-dir` parameter
- **Features**: Interactive dashboard, system information, detailed findings
- **Sections**: Executive summary, compliance metrics, detailed control results
- **System Info**: IP address, machine ID, distribution, scan timestamp

### CSV Report  
- **Default Location**: `./linux-cis-results.csv` (current directory)
- **Custom Location**: Use `--output-dir` parameter
- **Features**: Spreadsheet-compatible, filterable data
- **Columns**: Control ID, Title, Section, Status, Current State, Expected State, Evidence

## System Requirements

- **OS**: Ubuntu 22.04 LTS
- **Python**: 3.8+
- **Privileges**: Root access required for comprehensive scanning
- **Dependencies**: Standard Python libraries (json, subprocess, argparse, etc.)

## Architecture

### Scanner Engine
- **File**: `scripts/vijenex-cis.py`
- **Class**: `LinuxCISScanner`
- **Features**: Modular control execution, comprehensive reporting, error handling

### Milestone Structure
```
milestones/
├── milestone-1-1.json    # Filesystem Configuration
├── milestone-1-2.json    # Package Management
├── milestone-1-3.json    # Mandatory Access Controls
├── milestone-1-4.json    # Bootloader Configuration
├── milestone-2-1.json    # Server Services
├── milestone-2-2.json    # Client Services
├── milestone-2-3.json    # Service Clients
├── milestone-3-1.json    # Network Parameters (Host Only)
├── milestone-3-2.json    # Network Parameters (Host and Router)
├── milestone-4-1.json    # Host Based Firewall
├── milestone-5-1.json    # SSH Server
├── milestone-5-2.json    # Privilege Escalation
├── milestone-5-3.json    # PAM Configuration
├── milestone-5-4.json    # User Accounts and Environment
├── milestone-6-1.json    # System Logging
├── milestone-6-2.json    # System Auditing
├── milestone-6-3.json    # Filesystem Integrity Checking
├── milestone-7-1.json    # System File Permissions
└── milestone-7-2.json    # Local User and Group Settings
```

## Control Execution Flow

1. **Load Milestones**: JSON files containing control definitions
2. **Execute Controls**: Run appropriate check method based on control type
3. **Collect Results**: Gather status, current state, expected state, evidence
4. **Generate Reports**: Create HTML and CSV outputs with system information

## Security Features

- **Zero False Positives**: Carefully designed checks to avoid incorrect failures
- **Audit-Only Mode**: Scanner only reads system state, never modifies configuration
- **Comprehensive Logging**: Detailed evidence collection for each control
- **Error Handling**: Graceful handling of missing files, services, or permissions

## Enterprise Features

- **Professional Branding**: Vijenex Security Platform integration
- **Colorful CLI**: Enhanced user experience with status indicators
- **System Information**: Comprehensive system details in reports
- **Version Management**: Proper release versioning and tracking

## Compliance Mapping

This scanner implements controls from:
- **CIS Ubuntu Linux 22.04 LTS Benchmark v1.0.0**
- **Level 1**: Foundational security controls (recommended for all systems)
- **Level 2**: Enhanced security controls (for high-security environments)

## Command Line Options

```bash
usage: vijenex-cis.py [-h] [--output-dir OUTPUT_DIR] [--profile {Level1,Level2}]
                      [--milestones MILESTONES [MILESTONES ...]]
                      [--format {html,csv,both}]

Vijenex CIS - Ubuntu 22.04 LTS Security Compliance Scanner

options:
  -h, --help            show this help message and exit
  --output-dir OUTPUT_DIR
                        Output directory for reports
  --profile {Level1,Level2}
                        CIS profile level
  --milestones MILESTONES [MILESTONES ...]
                        Specific milestone files to scan
  --format {html,csv,both}
                        Report format
```

## Support

For issues, questions, or contributions:
- **Repository**: [Vijenex Linux CIS Scanner](https://github.com/vijenex/linux-cis-scanner)
- **Documentation**: See main repository README
- **License**: MIT License

---
**Powered by Vijenex Security Platform**