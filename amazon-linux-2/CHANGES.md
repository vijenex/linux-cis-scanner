# Amazon Linux 2 Scanner - Changes Applied

## Terminal Signature Updated

The terminal banner has been updated to show "Amazon Linux 2" instead of RHEL 8 references. The signature now displays:

```
=============================================================
                        VIJENEX                              
      Amazon Linux 2 CIS Scanner                      
           Powered by Vijenex Security Platform             
        https://github.com/vijenex/linux-cis-scanner        
=============================================================
```

This matches the style used in RHEL 8 and RHEL 9 scanners.

## Official Document Reference

The official CIS Amazon Linux 2 Benchmark v3.0.0 document is located at:
- `~/Downloads/CIS_Amazon_Linux_2_Benchmark_v3.0.0.pdf`

This document should be used as the reference for:
- Detailed control descriptions
- Remediation steps
- Rationale and impact statements
- CIS reference numbers

## Control List

The controls should be created based on the table of contents provided, which includes:

### Section 1 - Initial Setup
- 1.1 Filesystem (Kernel Modules, Partitions)
- 1.2 Configure Software and Patch Management
- 1.3 Configure Secure Boot Settings
- 1.4 Configure Additional Process Hardening
- 1.5 Mandatory Access Control (SELinux)
- 1.6 Configure Command Line Warning Banners

### Section 2 - Services
- 2.1 Configure Time Synchronization
- 2.2 Configure Special Purpose Services
- 2.3 Configure Service Clients

### Section 3 - Network
- 3.1 Configure Network Devices
- 3.2 Configure Network Kernel Modules
- 3.3 Configure Network Kernel Parameters
- 3.4 Configure Host Based Firewall

### Section 4 - Access, Authentication and Authorization
- 4.1 Configure job schedulers
- 4.2 Configure SSH Server
- 4.3 Configure privilege escalation
- 4.4 Configure Pluggable Authentication Modules
- 4.5 User Accounts and Environment

### Section 5 - Logging and Auditing
- 5.1 Configure Logging
- 5.2 Configure System Accounting (auditd)
- 5.3 Configure Integrity Checking

### Section 6 - System Maintenance
- 6.1 System File Permissions
- 6.2 Local User and Group Settings

## Next Steps

1. **Extract Controls from Official Document**: Use the PDF document to extract detailed control information including:
   - Control IDs
   - Titles
   - Descriptions
   - Remediation steps
   - Rationale
   - Impact statements
   - CIS references

2. **Create Milestone Files**: Create JSON milestone files for each section following the structure in:
   - `milestones/milestone-1-1.json` (example)
   - `milestones/milestone-1-2.json` (example)

3. **Validate Control Types**: Ensure each control uses the appropriate control type:
   - KernelModule
   - MountPoint
   - MountOption
   - ServiceStatus
   - PackageInstalled/PackageNotInstalled
   - SysctlParameter
   - FilePermissions
   - FileContent
   - SSHConfig
   - PAMConfig
   - SudoConfig
   - CommandOutputEmpty
   - FileExists

## Current Status

✅ Terminal signature updated to show "Amazon Linux 2"  
✅ Build system configured  
✅ Sample milestone files created (2 files)  
⏳ Full milestone files need to be created from official document  
⏳ Controls need to be validated against official benchmark

