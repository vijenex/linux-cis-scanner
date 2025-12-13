# Manual Controls Analysis - Path to 256+ Automated

## Current Status
- **Total Controls**: 447
- **Automated**: 234 (52%)
- **Manual**: 213 (48%)
- **Target**: 256+ automated (to match OpenSCAP)
- **Gap**: Need 22 more automated controls

## Manual Controls Breakdown

### 1. NO_TYPE Controls: 116 controls
**Problem**: These have `type: "NO_TYPE"` but many CAN be automated!

**Examples that CAN be automated:**
- `1.10.4, 1.10.5, 1.10.6` - File permissions checks → **FilePermissions type**
- `1.12.1` - AIDE installed → **PackageInstalled type**
- `1.7.1` - SELinux installed → **PackageInstalled type**
- `1.11.1` - Crypto policy check → **FileContent type**
- `1.12.2` - Cron job check → **CronJob type (NEW)**

**Action**: Change `type: "NO_TYPE"` to proper type and set `automated: true`

### 2. Manual Type: 65 controls
**Problem**: Marked as `type: "Manual"` but some can be automated

**Examples:**
- `1.1.1.11` - Unused filesystems → Can be automated with script
- `1.2.1.3` - repo_gpgcheck check → **FileContent type**

**Action**: Review each and convert automatable ones

### 3. PackageInstalled: 20 controls (ALREADY HAVE TYPE!)
**Problem**: These have correct type but `automated: false`

**Examples:**
- `2.2.1, 2.2.2, 2.2.3` - Package checks

**Action**: Simply change `automated: false` to `automated: true`

### 4. FilePermissions: 9 controls (ALREADY HAVE TYPE!)
**Problem**: These have correct type but `automated: false`

**Examples:**
- `5.1.1, 6.1.1, 6.1.2` - File permission checks

**Action**: Simply change `automated: false` to `automated: true`

### 5. ServiceStatus: 3 controls (ALREADY HAVE TYPE!)
**Problem**: These have correct type but `automated: false`

**Action**: Simply change `automated: false` to `automated: true`

---

## Quick Wins to Reach 256+ Automated

### Phase 1: Fix Existing Types (32 controls) ✅ EASY
Just change `automated: false` to `automated: true`:
- 20 PackageInstalled controls
- 9 FilePermissions controls  
- 3 ServiceStatus controls

**Result**: 234 + 32 = **266 automated** ✅ TARGET REACHED!

### Phase 2: Fix NO_TYPE Controls (50+ more)
Change `type: "NO_TYPE"` to proper type:
- FilePermissions: ~30 controls
- PackageInstalled: ~10 controls
- FileContent: ~10 controls

**Result**: 266 + 50 = **316 automated** 🚀

---

## Implementation Plan

### Step 1: Quick Fix - Change automated flag (5 minutes)
```python
# Find all controls with type but automated=false
# Change automated: false → automated: true
```

### Step 2: Fix NO_TYPE Controls (30 minutes)
```python
# Identify NO_TYPE controls
# Assign proper type based on audit command
# Set automated: true
```

### Step 3: Test Scanner (5 minutes)
```bash
sudo ./scan.sh
# Should show 266+ automated controls
```

---

## Control Types We Already Have Implemented

✅ **KernelModule** - Kernel module checks
✅ **MountPoint** - Partition checks
✅ **MountOption** - Mount option checks
✅ **ServiceStatus** - Systemd service checks
✅ **PackageInstalled** - RPM package checks
✅ **SysctlParameter** - Kernel parameter checks
✅ **FileContent** - File content/grep checks
✅ **FilePermissions** - File permission checks

## Control Types We Need (Optional - for Phase 2)

🔲 **CronJob** - Cron job checks (for 1.12.2)
🔲 **SSHConfig** - SSH configuration checks
🔲 **PAMConfig** - PAM configuration checks
🔲 **AuditRules** - Auditd rules checks

---

## Recommendation

**DO PHASE 1 NOW** - It's a 5-minute fix that gets us to 266 automated controls!

Just flip the `automated` flag on 32 controls that already have proper types implemented.

**Should I proceed with Phase 1 fix?**
