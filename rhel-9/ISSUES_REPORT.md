# RHEL 9 Scanner Issues Report

## Critical Issues

### 1. **Wrong Module Path and Branding (CRITICAL)**
   - **Location**: `go.mod`, `cmd/main.go`, `internal/scanner/scanner.go`
   - **Issue**: All imports and module name reference `rhel-8` instead of `rhel-9`
   - **Files Affected**:
     - `go.mod`: Line 1 - `module github.com/vijenex/linux-cis-scanner/rhel-8`
     - `cmd/main.go`: Line 10 - imports `rhel-8/internal/scanner`
     - `cmd/main.go`: Lines 23, 33, 67 - Text says "RHEL 8" instead of "RHEL 9"
     - `internal/scanner/scanner.go`: Lines 10-11 - imports `rhel-8/internal/controls` and `rhel-8/internal/report`
     - `internal/report/html.go`: Line 13 - HTML template title says "RHEL 8" instead of "RHEL 9"
   - **Impact**: Code won't compile correctly, wrong branding in output
   - **Fix**: Change all `rhel-8` references to `rhel-9`

### 2. **Incomplete ScanContext Initialization (CRITICAL)**
   - **Location**: `internal/controls/scancontext.go` - `BuildScanContext()` function
   - **Issue**: Only builds `Meta`, `Files`, and `Sysctl` contexts. Missing:
     - `Mounts` (Runtime and Fstab) - **NOT INITIALIZED**
     - `Services` - **NOT INITIALIZED**
     - `Packages` - **NOT INITIALIZED**
     - `Kernel` (LoadedModules, Blacklisted, Available) - **NOT INITIALIZED**
     - `SSH` - **NOT INITIALIZED**
     - `PAM` - **NOT INITIALIZED**
     - `Sudo` - **NOT INITIALIZED**
     - `Cron` - **NOT INITIALIZED**
   - **Impact**: 
     - Mount checks will fail with nil pointer or empty map errors
     - Kernel module checks will fail because `ctx.Kernel` is uninitialized
     - Any check trying to use these contexts will fail
   - **Evidence**: 
     - `CheckMountPoint()` and `CheckMountOption()` use `ctx.Mounts.Runtime` and `ctx.Mounts.Fstab` which are nil
     - `CheckKernelModule()` uses `ctx.GetModuleInfo()` which accesses uninitialized `ctx.Kernel` maps
   - **Fix**: Implement builder functions for all missing contexts

### 3. **Missing Context Builder Functions**
   - **Location**: `internal/controls/scancontext.go`
   - **Issue**: No functions to build:
     - `buildMountContext()` - Parse `/proc/mounts` and `/etc/fstab`
     - `buildServiceContext()` - Query systemd for service states
     - `buildPackageContext()` - Cache installed packages
     - `buildKernelContext()` - Load module info from `/proc/modules`, `/etc/modprobe.d/`
     - `buildSSHContext()` - Parse SSH config (partially exists in `ssh.go` but not integrated)
     - `buildPAMContext()` - Parse PAM files (partially exists in `pam.go` but not integrated)
     - `buildSudoContext()` - Parse sudoers (partially exists in `sudo.go` but not integrated)
     - `buildCronContext()` - Check cron file permissions
   - **Impact**: Context-dependent checks will fail or produce false positives

### 4. **Inconsistent Context Usage**
   - **Location**: Multiple files
   - **Issue**: 
     - Some checks use `ScanContext` (e.g., `CheckMountPoint`, `CheckKernelModule`) but context isn't fully built
     - Other checks don't use context at all (e.g., `CheckServiceStatus`, `CheckPackageInstalled`) and do direct file/command checks
     - This creates inconsistency and potential false positives
   - **Impact**: 
     - Unreliable results
     - Some checks may work while others fail
     - False positives when context is incomplete

### 5. **EvidenceCommand vs Evidence Inconsistency**
   - **Location**: `internal/scanner/scanner.go`, `internal/controls/results.go`
   - **Issue**: 
     - New code uses `Evidence` struct (Method, Source, Snippet)
     - Legacy code uses `EvidenceCommand` string
     - Scanner tries to use both: `result.EvidenceCommand = checkResult.Evidence.Source + ": " + checkResult.Evidence.Snippet`
     - Some checks return `EvidenceCommand`, others return `Evidence`
   - **Impact**: 
     - Inconsistent evidence reporting
     - Some results may have empty evidence
     - Report generation may fail or show incomplete data

## Logic and False Positive Issues

### 6. **Service Status Check Logic Issues**
   - **Location**: `internal/controls/checks.go` - `CheckServiceStatus()`
   - **Issue**: 
     - Only checks symlink existence for enabled services, doesn't verify actual systemd state
     - Doesn't check if service is masked
     - Logic for "disabled" is `!unitExists || !enabled` which may give false passes
     - Doesn't use systemd commands (`systemctl is-enabled`, `systemctl is-active`)
   - **Impact**: False positives/negatives for service status checks

### 7. **Kernel Module Check Issues**
   - **Location**: `internal/controls/checks.go` - `CheckKernelModule()`
   - **Issue**: 
     - Uses `BuildScanContext()` but `KernelContext` is never built
     - Accesses `ctx.Kernel.LoadedModules[module]` on uninitialized map (will return false, not error)
     - May incorrectly report modules as "not loaded" when they are
   - **Impact**: False negatives - may pass checks that should fail

### 8. **Mount Check Issues**
   - **Location**: `internal/controls/checks.go` - `CheckMountPoint()`, `CheckMountOption()`
   - **Issue**: 
     - Uses `ctx.Mounts.Runtime` and `ctx.Mounts.Fstab` which are never initialized
     - Will panic or return incorrect results
   - **Impact**: Mount checks will fail completely or produce false results

### 9. **FileContent Check - Missing Error Handling**
   - **Location**: `internal/controls/filecontent.go`
   - **Issue**: 
     - File size limit (1MB) may be too restrictive for some config files
     - No handling for binary files
     - Regex compilation errors are caught but may not be user-friendly
   - **Impact**: Some valid files may be rejected

### 10. **SSH Config Default Values**
   - **Location**: `internal/controls/ssh.go` - `getSSHDefault()`
   - **Issue**: 
     - Hardcoded defaults may not match actual OpenSSH defaults for RHEL 9
     - Some defaults marked as "but CIS wants" suggest they may be incorrect
   - **Impact**: False positives when parameter is not set (uses wrong default)

### 11. **PAM Config Check - Type Filter Missing**
   - **Location**: `internal/controls/pam.go` - `CheckPAMConfig()`
   - **Issue**: 
     - Line 175: `checkPAMParameter(entries, "", module, parameter, expected)` - PAM type is empty string
     - Should filter by PAM type (auth, account, password, session) for accurate checks
   - **Impact**: May match wrong PAM entry type, causing false positives/negatives

### 12. **Package Check - No Caching**
   - **Location**: `internal/controls/checks.go` - `CheckPackageInstalled()`
   - **Issue**: 
     - Runs `rpm -q` command for every check (no caching)
     - 10-second timeout may be too long or too short depending on system
     - Doesn't use `PackageContext` from ScanContext
   - **Impact**: 
     - Slow scans
     - Potential timeouts
     - Inconsistent with context-based approach

## Data Structure Issues

### 13. **MountInfo Options Map**
   - **Location**: `internal/controls/scancontext.go` - `MountInfo` struct
   - **Issue**: 
     - `Options map[string]bool` - boolean map doesn't preserve option values
     - Some mount options have values (e.g., `uid=1000`, `gid=1000`)
     - Current structure can't handle option values
   - **Impact**: Mount option checks may fail for options with values

### 14. **FileStat Missing UID/GID Population**
   - **Location**: `internal/controls/scancontext.go` - `getFileStat()`
   - **Issue**: 
     - `getFileStat()` doesn't populate `UID` and `GID` fields in `FileStat`
     - Only sets `Exists`, `IsRegular`, `IsSymlink`, `Mode`
   - **Impact**: File permission checks can't use cached FileStat, must re-read

## Missing Features

### 15. **No Error Recovery**
   - **Issue**: If one control fails, entire scan may fail
   - **Impact**: Partial results not available

### 16. **No Validation of Milestone JSON**
   - **Issue**: No schema validation for milestone JSON files
   - **Impact**: Invalid milestone files may cause runtime errors

### 17. **Missing Logging/Debugging**
   - **Issue**: Limited error messages, no debug mode
   - **Impact**: Hard to troubleshoot false positives

## Additional Issues Found

### 18. **HTML Report Template Wrong Version**
   - **Location**: `internal/report/html.go` - Line 13
   - **Issue**: HTML template title says "RHEL 8 CIS Compliance Report" instead of "RHEL 9"
   - **Impact**: Incorrect branding in generated HTML reports

## Summary

**Total Critical Issues**: 5
**Total Logic Issues**: 8
**Total Data Structure Issues**: 2
**Total Missing Features**: 3
**Total Branding Issues**: 2 (included in Critical #1)

**Priority Fix Order**:
1. Fix module path and branding (Issue #1)
2. Implement missing context builders (Issues #2, #3)
3. Fix context usage in checks (Issues #4, #6, #7, #8)
4. Standardize evidence handling (Issue #5)
5. Fix logic issues in checks (Issues #9-12)
6. Fix data structures (Issues #13-14)
7. Add missing features (Issues #15-17)

