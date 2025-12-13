# False Positive Analysis: Vijenex vs OpenSCAP

**Date**: December 13, 2024  
**Server**: ip-172-24-0-136 (RHEL 8)

---

## Summary

| Scanner | Passed | Failed | Manual | Total Automated |
|---------|--------|--------|--------|-----------------|
| **OpenSCAP** | 152 | 104 | N/A | 256 |
| **Vijenex** | 67 | 122 | 181 | 189 |

**Key Findings:**
- OpenSCAP automated: 256 controls
- Vijenex automated: 189 controls (67 less - likely Level 2 controls skipped)
- OpenSCAP has MORE passes (152 vs 67)
- Vijenex has MORE failures (122 vs 104)

---

## Critical Discrepancies Found

### 1. Mount Options - FALSE POSITIVES in Vijenex ⚠️

**Vijenex shows FAIL:**
```
1.1.2.1.2 - nodev option on /tmp (FAIL)
1.1.2.1.3 - nosuid option on /tmp (FAIL)
1.1.2.1.4 - noexec option on /tmp (FAIL)
1.1.2.2.4 - noexec option on /dev/shm (FAIL)
1.1.2.3.2 - nodev option on /home (FAIL)
1.1.2.3.3 - nosuid option on /home (FAIL)
... 12 more mount option failures
```

**OpenSCAP shows:**
```
Add nodev Option to /tmp     - notapplicable
Add noexec Option to /tmp    - notapplicable
Add nosuid Option to /tmp    - notapplicable
Add nosuid Option to /home   - notapplicable
Add nodev Option to /var/tmp - notapplicable
Add noexec Option to /var/tmp - notapplicable
```

**Analysis:**
- OpenSCAP marks these as "notapplicable" (partitions don't exist separately)
- Vijenex marks them as FAIL
- **This is a FALSE POSITIVE** - Vijenex should check if partition exists first
- If partition doesn't exist, should be SKIPPED or NOTAPPLICABLE, not FAIL

**Impact:** ~18 false positive failures

---

### 2. Kernel Modules - Need Verification

**Both show FAIL:**
```
cramfs kernel module       - OpenSCAP: FAIL, Vijenex: FAIL
usb-storage kernel module  - OpenSCAP: (not shown), Vijenex: FAIL
```

**Need to verify on server:**
```bash
lsmod | grep cramfs
lsmod | grep usb_storage
modprobe -n -v cramfs
modprobe -n -v usb_storage
```

**If modules are blacklisted:** These are REAL failures (correct)  
**If modules are not loaded:** These might be false positives

---

### 3. AIDE - Both Agree (REAL Failures)

**Both show FAIL:**
```
Install AIDE                    - OpenSCAP: FAIL, Vijenex: (need to check)
Build and Test AIDE Database    - OpenSCAP: FAIL, Vijenex: (need to check)
Configure AIDE to Verify Tools  - OpenSCAP: FAIL, Vijenex: (need to check)
Configure Periodic AIDE         - OpenSCAP: FAIL, Vijenex: (need to check)
```

**Analysis:** These are REAL failures - AIDE is not configured

---

### 4. SELinux - Discrepancy

**Vijenex shows FAIL:**
```
1.3.1.1 - Ensure SELinux is installed (FAIL)
1.3.1.3 - Ensure SELinux policy is configured (FAIL)
1.3.1.4 - Ensure SELinux mode is not disabled (FAIL)
```

**OpenSCAP shows:**
```
Install libselinux Package              - PASS
Configure SELinux Policy                - PASS
Ensure SELinux Not Disabled in grub     - PASS
Ensure SELinux is Not Disabled          - FAIL
```

**Analysis:**
- OpenSCAP shows SELinux IS installed (PASS)
- Vijenex shows SELinux NOT installed (FAIL)
- **This is a FALSE POSITIVE in Vijenex** - SELinux is installed
- Vijenex might be checking wrong package name or wrong condition

**Impact:** ~3 false positive failures

---

### 5. /tmp Partition - Both Agree (REAL Failure)

**Both show FAIL:**
```
Ensure /tmp Located On Separate Partition - OpenSCAP: FAIL, Vijenex: FAIL
```

**Analysis:** This is a REAL failure - /tmp is not a separate partition

---

## Detailed Comparison by Category

### Kernel Modules
| Control | Vijenex | OpenSCAP | Likely Correct |
|---------|---------|----------|----------------|
| cramfs | FAIL | FAIL | REAL failure |
| usb-storage | FAIL | (not shown) | Need verification |

### Mount Options (18 controls)
| Control | Vijenex | OpenSCAP | Likely Correct |
|---------|---------|----------|----------------|
| /tmp nodev | FAIL | notapplicable | FALSE POSITIVE |
| /tmp nosuid | FAIL | notapplicable | FALSE POSITIVE |
| /tmp noexec | FAIL | notapplicable | FALSE POSITIVE |
| /home nodev | FAIL | notapplicable | FALSE POSITIVE |
| /home nosuid | FAIL | notapplicable | FALSE POSITIVE |
| /var nodev | FAIL | notapplicable | FALSE POSITIVE |
| /var nosuid | FAIL | notapplicable | FALSE POSITIVE |
| /var/tmp nodev | FAIL | notapplicable | FALSE POSITIVE |
| /var/tmp nosuid | FAIL | notapplicable | FALSE POSITIVE |
| /var/tmp noexec | FAIL | notapplicable | FALSE POSITIVE |
| /var/log nodev | FAIL | notapplicable | FALSE POSITIVE |
| /var/log nosuid | FAIL | notapplicable | FALSE POSITIVE |
| /var/log noexec | FAIL | notapplicable | FALSE POSITIVE |
| /var/log/audit nodev | FAIL | notapplicable | FALSE POSITIVE |
| /var/log/audit nosuid | FAIL | notapplicable | FALSE POSITIVE |
| /var/log/audit noexec | FAIL | notapplicable | FALSE POSITIVE |
| /dev/shm noexec | FAIL | PASS | FALSE POSITIVE |

**Total: ~17 false positives**

### SELinux
| Control | Vijenex | OpenSCAP | Likely Correct |
|---------|---------|----------|----------------|
| SELinux installed | FAIL | PASS | FALSE POSITIVE |
| SELinux policy | FAIL | PASS | FALSE POSITIVE |
| SELinux not disabled | FAIL | FAIL | REAL failure |

**Total: ~2 false positives**

### AIDE
| Control | Vijenex | OpenSCAP | Likely Correct |
|---------|---------|----------|----------------|
| Install AIDE | (check) | FAIL | REAL failure |
| Build AIDE DB | (check) | FAIL | REAL failure |
| Configure AIDE | (check) | FAIL | REAL failure |
| Periodic AIDE | (check) | FAIL | REAL failure |

---

## Summary of False Positives

### Confirmed False Positives in Vijenex: ~19-22

1. **Mount Options** (~17): Checking mount options on non-existent partitions
2. **SELinux** (~2-3): Incorrectly detecting SELinux as not installed

### Root Causes

#### 1. Mount Option Checks
**Problem:** Vijenex checks mount options even when partition doesn't exist

**Fix Needed:**
```go
// In controls/mount.go
func CheckMountOption(mountPoint, option string) CheckResult {
    // First check if mount point exists
    if !mountPointExists(mountPoint) {
        return CheckResult{
            Status: "SKIPPED",
            Description: "Partition does not exist",
        }
    }
    // Then check for option
    ...
}
```

#### 2. SELinux Checks
**Problem:** Vijenex might be checking wrong package or wrong condition

**Fix Needed:**
```go
// Check for correct package names
packages := []string{"libselinux", "selinux-policy", "selinux-policy-targeted"}
// Or check if SELinux is actually running
selinuxStatus := exec.Command("getenforce").Output()
```

---

## Recommendations

### Immediate Fixes Required

1. **Fix Mount Option Checks**
   - Add partition existence check before checking mount options
   - Return SKIPPED/NOTAPPLICABLE if partition doesn't exist
   - This will fix ~17 false positives

2. **Fix SELinux Checks**
   - Verify correct package names
   - Check actual SELinux status, not just package installation
   - This will fix ~2-3 false positives

3. **Re-test After Fixes**
   - Rebuild scanner
   - Run on same server
   - Compare with OpenSCAP again
   - Verify false positives are fixed

### Expected Results After Fixes

**Current:**
- Vijenex: 67 pass, 122 fail (189 automated)
- False positives: ~19-22

**After fixes:**
- Vijenex: 67 pass, ~100 fail (189 automated)
- False positives: <5
- Results should match OpenSCAP more closely

---

## Verification Commands

### On RHEL 8 Server

```bash
# Check mount points
df -h
mount | grep -E "(tmp|home|var)"

# Check if /tmp is separate partition
findmnt /tmp

# Check SELinux
rpm -q libselinux selinux-policy
getenforce
sestatus

# Check kernel modules
lsmod | grep -E "(cramfs|usb_storage)"
modprobe -n -v cramfs
modprobe -n -v usb_storage

# Check AIDE
rpm -q aide
ls -l /etc/cron.d/aide
```

---

## Action Items

- [ ] Fix mount option checks to handle non-existent partitions
- [ ] Fix SELinux checks to use correct detection method
- [ ] Rebuild scanner binaries
- [ ] Re-run scan on same server
- [ ] Compare results with OpenSCAP again
- [ ] Verify false positive count is <5
- [ ] Document remaining differences

---

## Conclusion

**Vijenex has ~19-22 false positives** compared to OpenSCAP, primarily in:
1. Mount option checks on non-existent partitions (~17)
2. SELinux detection (~2-3)

These are **fixable** and should be corrected before production deployment.

After fixes, Vijenex should have similar failure counts to OpenSCAP (within 10-20 controls).
