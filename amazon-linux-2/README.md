# Amazon Linux 2 CIS Scanner

This directory contains the Vijenex CIS Scanner implementation for Amazon Linux 2, following the same architecture as the RHEL 8 and RHEL 9 scanners.

## Structure

```
amazon-linux-2/
├── go-scanner/
│   ├── cmd/              # Main application entry point
│   ├── internal/         # Internal packages
│   │   ├── controls/     # Control check implementations
│   │   ├── scanner/      # Scanner logic
│   │   └── report/       # Report generation (HTML, CSV)
│   ├── milestones/       # Control milestone JSON files
│   ├── bin/              # Build output directory
│   ├── build.sh          # Build script
│   ├── Makefile          # Build automation
│   ├── go.mod            # Go module definition
│   └── README.md         # Detailed documentation
```

## Quick Start

### Build

```bash
cd amazon-linux-2/go-scanner
./build.sh
```

Or using Make:

```bash
make build-linux
```

### Run

```bash
sudo ./bin/vijenex-cis-amd64 --output-dir ./reports
```

## Milestone Files

Milestone files define groups of controls organized by CIS Benchmark sections. Currently, sample milestone files are provided for:

- `milestone-1-1.json`: Section 1.1.1 - Filesystem Kernel Modules
- `milestone-1-2.json`: Section 1.1.2 - Configure Filesystem Partitions

### Adding More Milestones

Based on the CIS Amazon Linux 2 Benchmark table of contents, you'll need to create milestone files for:

1. **Section 1 - Initial Setup**
   - 1.1 Filesystem (partial - in progress)
   - 1.2 Configure Software and Patch Management
   - 1.3 Configure Secure Boot Settings
   - 1.4 Configure Additional Process Hardening
   - 1.5 Mandatory Access Control (SELinux)
   - 1.6 Configure Command Line Warning Banners

2. **Section 2 - Services**
   - 2.1 Configure Time Synchronization
   - 2.2 Configure Special Purpose Services
   - 2.3 Configure Service Clients

3. **Section 3 - Network**
   - 3.1 Configure Network Devices
   - 3.2 Configure Network Kernel Modules
   - 3.3 Configure Network Kernel Parameters
   - 3.4 Configure Host Based Firewall

4. **Section 4 - Access, Authentication and Authorization**
   - 4.1 Configure job schedulers
   - 4.2 Configure SSH Server
   - 4.3 Configure privilege escalation
   - 4.4 Configure Pluggable Authentication Modules
   - 4.5 User Accounts and Environment

5. **Section 5 - Logging and Auditing**
   - 5.1 Configure Logging
   - 5.2 Configure System Accounting (auditd)
   - 5.3 Configure Integrity Checking

6. **Section 6 - System Maintenance**
   - 6.1 System File Permissions
   - 6.2 Local User and Group Settings

## Control Types Supported

The scanner supports all control types from RHEL 8/9:

- `KernelModule` - Check kernel module availability
- `MountPoint` - Verify separate partition existence
- `MountOption` - Check mount options
- `ServiceStatus` - Verify service status
- `PackageInstalled` - Check package installation
- `PackageNotInstalled` - Verify package removal
- `SysctlParameter` - Check sysctl parameters
- `FilePermissions` - Verify file permissions
- `FileContent` - Check file content patterns
- `SSHConfig` - Verify SSH configuration
- `PAMConfig` - Check PAM configuration
- `SudoConfig` - Verify sudo configuration
- `CommandOutputEmpty` - Check command output
- `FileExists` - Verify file existence

## Example Milestone Structure

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

## Next Steps

1. **Complete Milestone Files**: Create milestone JSON files for all sections based on the CIS Amazon Linux 2 Benchmark
2. **Test Controls**: Verify each control type works correctly on Amazon Linux 2
3. **Validate Against Benchmark**: Compare results with official CIS benchmark
4. **Documentation**: Update documentation with Amazon Linux 2-specific notes

## Differences from RHEL 8/9

Amazon Linux 2 is based on RHEL 7, so some differences may exist:

- Package manager: Uses `yum` (not `dnf`)
- Systemd: Uses systemd but may have different service names
- SELinux: Uses SELinux but configuration may differ
- File paths: Some configuration file paths may differ

## References

- [CIS Amazon Linux 2 Benchmark](https://www.cisecurity.org/benchmark/amazon_linux)
- [RHEL 8 Scanner](../rhel-8/go-scanner/README.md) - Reference implementation
- [RHEL 9 Scanner](../rhel-9/go-scanner/README.md) - Reference implementation

