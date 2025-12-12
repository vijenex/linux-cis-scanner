# Changelog

## [1.0.0] - 2025-01-XX

### Added
- ✅ 234 automated controls (91% of OpenSCAP target)
- ✅ 447 total controls across all CIS sections
- ✅ 8 control types implemented:
  - KernelModule
  - MountPoint
  - MountOption
  - ServiceStatus
  - PackageInstalled
  - FileContent
  - SysctlParameter (NEW)
  - FilePermissions (NEW)
- ✅ Automated control extraction script (auto-add-controls.py)
- ✅ Professional HTML reports with severity breakdown
- ✅ CSV export functionality
- ✅ 48 milestone files organized by CIS section
- ✅ Comprehensive documentation (README.md, INSTRUCTIONS.md)

### Implemented Control Types
1. **KernelModule** - 16 controls
2. **ServiceStatus** - 23 controls
3. **SysctlParameter** - 23 controls
4. **MountOption** - 19 controls
5. **PackageInstalled** - 12 controls
6. **MountPoint** - 7 controls
7. **FilePermissions** - 7 controls
8. **FileContent** - 127 controls

### Features
- Automatic milestone file organization by section
- Level 1 and Level 2 profile support
- Impact warnings for Level 2 controls
- Expandable control details in HTML report
- Compliance score calculation
- Severity-based failure categorization

### Testing Status
- ⚠️ Pending: Real RHEL 8 system testing
- ⚠️ Pending: OpenSCAP comparison validation
- ⚠️ Pending: False positive verification

### Known Limitations
- Need 22 more controls to reach 256+ target
- Some FileContent checks need refinement
- SSHConfig, PAMConfig, AuditRules types not yet implemented
- No automated remediation (by design - safety first)

### Next Release Goals
- Reach 256+ automated controls
- Validate accuracy against OpenSCAP
- Fix any false positives
- Add remaining control types if needed
- Multi-machine scanning support
- Consolidated reporting for 50+ machines
