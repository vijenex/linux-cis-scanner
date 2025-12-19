# RHEL 9 Scanner - Critical Issues Summary

## Top 5 Issues Causing False Positives & Bugs

### 1. **Incomplete ScanContext - CAUSES MOST FALSE POSITIVES**
**Why it's critical**: The `BuildScanContext()` function only initializes 3 out of 10 required contexts. This means:
- **Mount checks will FAIL** - `ctx.Mounts.Runtime` and `ctx.Mounts.Fstab` are nil/empty maps
- **Kernel module checks will FAIL** - `ctx.Kernel` maps are uninitialized, always returns false
- **Any check using these contexts will produce incorrect results**

**Location**: `internal/controls/scancontext.go:140-148`

**Current code**:
```go
func BuildScanContext() (*ScanContext, error) {
    ctx := &ScanContext{}
    ctx.Meta = buildMeta()
    ctx.Files = buildFileContext()
    ctx.Sysctl = buildSysctlContext()
    // TODO: Add other builders incrementally  <-- MISSING!
    return ctx, nil
}
```

**Missing builders**:
- `buildMountContext()` - Parse `/proc/mounts` and `/etc/fstab`
- `buildKernelContext()` - Load from `/proc/modules`, `/etc/modprobe.d/`
- `buildServiceContext()` - Query systemd
- `buildPackageContext()` - Cache RPM queries
- `buildSSHContext()`, `buildPAMContext()`, `buildSudoContext()`, `buildCronContext()`

---

### 2. **Wrong Module Path - WON'T COMPILE**
**Why it's critical**: All imports reference `rhel-8` instead of `rhel-9`, causing compilation failures.

**Files to fix**:
- `go.mod`: Change module name from `rhel-8` to `rhel-9`
- `cmd/main.go`: Line 10 - Change import path
- `internal/scanner/scanner.go`: Lines 10-11 - Change import paths

---

### 3. **Mount Checks Access Nil Maps**
**Why it's critical**: `CheckMountPoint()` and `CheckMountOption()` try to access maps that were never initialized, causing panics or always-fail results.

**Location**: `internal/controls/checks.go:47-122`

**Problem code**:
```go
func CheckMountPoint(mountPoint, expectedStatus string) CheckResult {
    ctx, _ := BuildScanContext()
    // ctx.Mounts.Runtime is nil/empty - will always fail!
    if mountInfo, exists := ctx.Mounts.Runtime[mountPoint]; exists {
        // This will never execute
    }
}
```

---

### 4. **Kernel Module Checks Always Return False**
**Why it's critical**: `CheckKernelModule()` accesses uninitialized maps, so module status is always reported incorrectly.

**Location**: `internal/controls/checks.go:12-45`

**Problem**: 
- `ctx.Kernel.LoadedModules[module]` on nil map returns `false` (zero value)
- `ctx.Kernel.Blacklisted[module]` on nil map returns `false`
- `ctx.Kernel.Available[module]` on nil map returns `false`
- Result: All modules appear as "not loaded, not blacklisted, not available" = **FALSE PASSES**

---

### 5. **Inconsistent Evidence Handling**
**Why it's critical**: Mix of `EvidenceCommand` (string) and `Evidence` (struct) causes some results to have empty evidence fields.

**Location**: `internal/scanner/scanner.go` - Multiple places

**Problem**: 
- Some checks return `checkResult.EvidenceCommand` (legacy)
- Others return `checkResult.Evidence` (new struct)
- Scanner tries to use both: `result.EvidenceCommand = checkResult.Evidence.Source + ": " + checkResult.Evidence.Snippet`
- If `EvidenceCommand` is empty, this creates malformed evidence strings

---

## Quick Fix Priority

1. **Fix module path** (5 minutes) - Change all `rhel-8` to `rhel-9`
2. **Implement missing context builders** (2-3 hours) - This fixes most false positives
3. **Fix mount/kernel checks** (30 minutes) - After context is built
4. **Standardize evidence** (1 hour) - Choose one format

---

## Impact Assessment

| Issue | False Positives | False Negatives | Crashes | Total Impact |
|-------|----------------|-----------------|---------|--------------|
| Incomplete Context | **HIGH** | **HIGH** | Medium | **CRITICAL** |
| Wrong Module Path | N/A | N/A | **HIGH** | **CRITICAL** |
| Mount Checks | **HIGH** | Low | Medium | **HIGH** |
| Kernel Checks | **HIGH** | **HIGH** | Low | **HIGH** |
| Evidence Handling | Low | Low | Low | Medium |

---

## Recommended Fix Order

1. **Day 1**: Fix module path + implement `buildMountContext()` and `buildKernelContext()`
2. **Day 2**: Implement remaining context builders (`Service`, `Package`, `SSH`, `PAM`, `Sudo`, `Cron`)
3. **Day 3**: Fix evidence handling, add error recovery, improve logging

This will resolve ~80% of false positives and bugs.

