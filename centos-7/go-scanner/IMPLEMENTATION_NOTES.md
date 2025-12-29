# CentOS 7 Scanner Implementation Notes

## Overview

This scanner is built based on lessons learned from RHEL 8 and RHEL 9 implementations, with all false positive fixes applied.

## Key Features

### 1. False Positive Fixes Applied

All fixes from RHEL 8/9 have been applied:

- **Mount Options**: Returns `NOT_APPLICABLE` when partition doesn't exist (not `FAIL`)
- **Complete ScanContext**: All context builders implemented (mount, kernel, service, package, SSH, PAM, sudo, cron)
- **Context Caching**: Packages and services are cached for performance
- **Proper Error Handling**: All context builders have error handling

### 2. Level 2 Controls Excluded

As per requirements:
- All Level 2 controls are excluded from milestone JSON files
- Scanner will skip Level 2 controls if they appear in milestones

### 3. Unsupported Controls Excluded

Controls that don't apply to CentOS 7 are excluded from milestones.

## Implementation Details

### ScanContext

Complete implementation with all builders:
- `buildMeta()` - System metadata
- `buildFileContext()` - File stat cache
- `buildSysctlContext()` - Runtime + persistent sysctl
- `buildMountContext()` - Runtime mounts + fstab
- `buildKernelContext()` - Kernel modules (loaded, blacklisted, available)
- `buildServiceContext()` - Systemd service states
- `buildPackageContext()` - Installed packages cache
- `buildSSHContext()` - SSH configuration
- `buildPAMContext()` - PAM configuration
- `buildSudoContext()` - Sudo defaults
- `buildCronContext()` - Cron file permissions

### Checks with Context

All checks use ScanContext:
- `CheckKernelModule()` - Uses KernelContext
- `CheckMountPoint()` - Uses MountContext
- `CheckMountOption()` - Uses MountContext (returns NOT_APPLICABLE if partition missing)
- `CheckServiceStatus()` - Uses ServiceContext with fallback
- `CheckPackageInstalled()` - Uses PackageContext cache
- `CheckSysctlParameter()` - Uses SysctlContext

### Mount Option Fix

The critical fix for mount options:

```go
func CheckMountOption(mountPoint, requiredOption string) CheckResult {
    ctx, err := BuildScanContext()
    if err != nil {
        return Error(err, "context")
    }
    
    mountInfo, runtimeExists := ctx.Mounts.Runtime[mountPoint]
    if !runtimeExists {
        // CIS semantics: if partition doesn't exist, it's NOT_APPLICABLE
        return NotApplicable(
            fmt.Sprintf("Mount point %s not configured as separate partition", mountPoint),
            "mount not found",
        )
    }
    // ... rest of check
}
```

This prevents false positives when checking mount options on partitions that don't exist.

## Milestone Files

**IMPORTANT**: Milestone JSON files need to be generated from the official CIS PDF:
`CIS_CentOS_Linux_7_Benchmark_v3.1.2.pdf`

The milestone files should:
1. Include only Level 1 controls
2. Exclude Level 2 controls
3. Exclude unsupported controls
4. Use official ID, title, description, and remediation from the PDF

## Testing Checklist

Before deployment, verify:
- [ ] Scanner compiles without errors
- [ ] All context builders work correctly
- [ ] Mount options return NOT_APPLICABLE for non-existent partitions
- [ ] No false positives in test scans
- [ ] Level 2 controls are excluded
- [ ] Reports generate correctly (CSV and HTML)

## Next Steps

1. **Generate Milestone Files**: Extract controls from `CIS_CentOS_Linux_7_Benchmark_v3.1.2.pdf`
2. **Test on CentOS 7**: Run scanner on actual CentOS 7 system
3. **Verify Results**: Compare with manual checks to ensure no false positives
4. **Build Binaries**: Run `./build.sh` to create distribution binaries

## References

- RHEL 8 False Positive Analysis: `rhel-8/FALSE_POSITIVE_ANALYSIS.md`
- RHEL 9 Fixes Applied: `rhel-9/FIXES_APPLIED.md`
- RHEL 9 Critical Issues: `rhel-9/CRITICAL_ISSUES_SUMMARY.md`

