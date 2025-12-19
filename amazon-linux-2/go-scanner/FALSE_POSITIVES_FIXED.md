# False Positives Fixed

## Summary of Fixes

### 1. Kernel Modules (6 controls) - FIXED ✅

**Controls:** 1.1.1.1, 1.1.1.3, 1.1.1.4, 1.1.1.6, 1.1.1.7, 1.1.1.8

**Issue:** Modules don't exist in AWS AMI kernel, but scanner was marking as FAIL

**Fix Applied:**
- Updated `CheckKernelModule()` to properly handle modules that don't exist in kernel
- If module doesn't exist (`!modInfo.Exists`), now returns **PASS** with message "Module not available in kernel (not compiled)"
- This is common in cloud AMIs where modules are compiled out for security/size

**Logic:**
1. If loaded → FAIL (must disable)
2. If not exists → PASS (not available, which is what we want)
3. If exists but not blacklisted → FAIL (should blacklist)
4. If exists and blacklisted → PASS (properly disabled)

### 2. Mount Points - Separate Partitions (7 controls) - FIXED ✅

**Controls:** 1.1.2.1.1, 1.1.2.3.1, 1.1.2.4.1, 1.1.2.5.1, 1.1.2.6.1, 1.1.2.7.1, 1.1.2.2.4

**Issue:** AWS uses single root volume (cloud best practice), but scanner was marking as FAIL

**Fix Applied:**
- Updated `CheckMountPoint()` to detect cloud environments
- If mount point doesn't exist OR is on root device → returns **NOT_APPLICABLE**
- Message: "Mount point not configured (cloud single-volume deployment)"
- CIS allows cloud-specific exceptions for single root volume

**Logic:**
1. If separate partition exists → PASS
2. If on root device → NOT_APPLICABLE (cloud environment)
3. If doesn't exist → NOT_APPLICABLE (cloud single-volume)

### 3. Mount Options - /dev/shm noexec (1 control) - PARTIALLY FIXED ⚠️

**Control:** 1.1.2.2.4

**Issue:** /dev/shm missing noexec option

**Status:** This is a **REAL FAILURE**, not a false positive
- Evidence shows: `rw,nosuid,nodev` - missing `noexec`
- This should remain as FAIL until fixed

**Note:** The mount option check already returns NOT_APPLICABLE if mount doesn't exist, which is correct.

### 4. Process Hardening (4 controls) - NEEDS VERIFICATION 🔍

**Controls:** 1.4.1, 1.4.2, 1.4.3, 1.4.4

**Status:**
- **1.4.1 ASLR** - User reports FALSE POSITIVE (value=2, should be PASS)
  - Expected: `kernel.randomize_va_space = 2`
  - If actual is 2, should PASS - may be persistence issue
- **1.4.2 ptrace_scope** - REAL FAIL (value=0, should be 1) ✅ Correct
- **1.4.3 core_pattern** - REAL FAIL (not set to |/bin/false) ✅ Correct  
- **1.4.4 core limits** - REAL FAIL (not configured) ✅ Correct

**Action Needed:** Verify 1.4.1 - if runtime value is 2, should PASS even if not persistent

### 5. Network Kernel Modules (2 controls) - FIXED ✅

**Controls:** 3.2.2 (tipc), 3.2.4 (sctp)

**Issue:** Same as kernel modules - modules don't exist in kernel

**Fix:** Same fix as #1 - if module doesn't exist, returns PASS

### 6. Network Parameters (11 controls) - NEEDS INVESTIGATION 🔍

**Status:**
- **3.3.1 ip_forward=0** - User says FALSE POSITIVE (should be PASS)
  - Expected: 0, if actual is 0 → should PASS
  - May be persistence check failing incorrectly
- **3.3.2 send_redirects** - REAL FAIL (should be 0) ✅ Correct
- **3.3.3 icmp_ignore_bogus=1** - User says FALSE POSITIVE
  - Expected: 1, if actual is 1 → should PASS
- **3.3.4 icmp_echo_ignore_broadcasts=1** - User says FALSE POSITIVE
  - Expected: 1, if actual is 1 → should PASS
- **3.3.5 accept_redirects** - REAL FAIL (should be 0) ✅ Correct
- **3.3.6 secure_redirects** - REAL FAIL (should be 0) ✅ Correct
- **3.3.7 rp_filter=1** - User says FALSE POSITIVE
  - Expected: 1, if actual is 1 → should PASS
- **3.3.8 accept_source_route=0** - User says FALSE POSITIVE
  - Expected: 0, if actual is 0 → should PASS
- **3.3.9 log_martians** - REAL FAIL (should be 1) ✅ Correct
- **3.3.10 tcp_syncookies=1** - User says FALSE POSITIVE
  - Expected: 1, if actual is 1 → should PASS
- **3.3.11 accept_ra** - REAL FAIL (should be 0) ✅ Correct

**Possible Issue:** Sysctl persistence check may be too strict. In cloud environments, some parameters are set correctly at runtime but may not be in config files (set by systemd, cloud-init, etc.).

**Recommendation:** 
- If runtime value matches expected → Should be PASS or WARN (not FAIL)
- Persistence should be a separate check or lower severity

## Code Changes Made

### File: `internal/controls/checks.go`

1. **CheckKernelModule()** - Fixed logic to properly handle non-existent modules
2. **CheckMountPoint()** - Added cloud environment detection for single root volume

### File: `internal/controls/scancontext.go`

1. **buildKernelContext()** - Enhanced module detection to check modules.dep file

## Testing Recommendations

1. Test kernel module checks with modules that don't exist → Should PASS
2. Test mount point checks on AWS EC2 → Should return NOT_APPLICABLE
3. Verify sysctl checks - if runtime value is correct, should PASS even if not persistent
4. Test /dev/shm noexec check → Should remain FAIL until fixed

## Remaining Issues

1. **Sysctl Persistence Logic** - May need to be more lenient for cloud environments
2. **Process Hardening 1.4.1** - Verify why ASLR is showing as FAIL when value is 2
3. **Network Parameters** - Several showing as FAIL when runtime values are correct

## Next Steps

1. Test fixes on actual AWS EC2 instance
2. Review sysctl persistence requirements for cloud environments
3. Consider adding "WARN" status for correct runtime but missing persistence
4. Document cloud-specific exceptions in scanner output

