# 🎯 AUTOMATION PRIORITY: 60 Missing Controls

Based on smart analysis comparing OpenSCAP automated vs Vijenex manual controls.

## 📊 **THE 60 MISSING AUTOMATED CONTROLS**

### **Priority 1: Quick Wins (20 controls)**

#### **1. AIDE Controls (4 controls)**
- ✅ Already have PackageInstalled type
- Need: ServiceStatus + FileContent checks

**Vijenex Manual → Should be Automated:**
- 1.12.1 Ensure AIDE is installed → **PackageInstalled** (aide)
- 1.12.2 Ensure filesystem integrity is regularly checked → **FileContent** (/etc/cron.d/aide)

#### **2. Banner Controls (2 controls)**  
- ✅ Already have FileContent type
- Need: File permission checks

**Vijenex Manual → Should be Automated:**
- 1.10.2 Ensure local login warning banner is configured properly → **FileContent** (/etc/issue)
- 1.10.3 Ensure remote login warning banner is configured properly → **FileContent** (/etc/issue.net)

#### **3. Cron Permission Controls (6 controls)**
- ✅ Already have FilePermissions type
- Need: Apply to cron directories

**Vijenex Manual → Should be Automated:**
- 6.5.1 Ensure permissions on /etc/crontab are configured → **FilePermissions**
- 6.5.2 Ensure permissions on /etc/cron.hourly are configured → **FilePermissions**
- 6.5.3 Ensure permissions on /etc/cron.daily are configured → **FilePermissions**
- 6.5.4 Ensure permissions on /etc/cron.weekly are configured → **FilePermissions**
- 6.5.5 Ensure permissions on /etc/cron.monthly are configured → **FilePermissions**
- 6.5.6 Ensure permissions on /etc/cron.d are configured → **FilePermissions**

#### **4. File Permission Controls (3 controls)**
- ✅ Already have FilePermissions type
- Need: World-writable file checks

**Vijenex Manual → Should be Automated:**
- 6.1.9 Ensure no world writable files exist → **Custom check**
- 6.1.12 Ensure sticky bit is set on all world-writable directories → **Custom check**
- 7.1.13 Ensure SUID and SGID files are reviewed → **Custom check**

#### **5. Umask Controls (3 controls)**
- ✅ Already have FileContent type
- Need: Check umask in config files

**Vijenex Manual → Should be Automated:**
- Check umask in /etc/bashrc, /etc/profile, /etc/login.defs

#### **6. Journald/Rsyslog Controls (2 controls)**
- ✅ Already have FileContent type
- Need: Check journald.conf settings

### **Priority 2: Medium Effort (25 controls)**

#### **7. SSH Controls (13 controls)**
- ✅ Already have FileContent type
- Need: SSH config parser

**All SSH controls in section 5.1.x and 5.2.x**

#### **8. Network Parameters (12 controls)**
- ✅ Already have SysctlParameter type
- Need: Add IPv4/IPv6 parameters

**All network sysctl parameters in section 3.3.x**

### **Priority 3: Complex (15 controls)**

#### **9. PAM/Password Controls (12 controls)**
- ❌ Need new PAMConfig type
- Complex PAM module parsing

#### **10. Sudo Controls (3 controls)**
- ❌ Need new SudoConfig type
- Parse /etc/sudoers

## 🚀 **IMPLEMENTATION PLAN**

### **Phase 1: Quick Wins (1-2 days)**
1. Add 4 AIDE controls → **PackageInstalled + FileContent**
2. Add 2 Banner controls → **FileContent**  
3. Add 6 Cron controls → **FilePermissions**
4. Add 3 File permission controls → **Custom checks**
5. Add 3 Umask controls → **FileContent**
6. Add 2 Journald controls → **FileContent**

**Result: +20 automated controls (216 total)**

### **Phase 2: SSH + Network (2-3 days)**
1. Add SSH config parser → **SSHConfig type**
2. Add network parameters → **SysctlParameter**

**Result: +25 automated controls (241 total)**

### **Phase 3: PAM + Sudo (3-4 days)**
1. Create PAMConfig type
2. Create SudoConfig type

**Result: +15 automated controls (256 total = matches OpenSCAP!)**

## 📋 **IMMEDIATE ACTION**

**Start with Phase 1 - can be done TODAY:**

1. **AIDE**: Change 1.12.1 from manual to PackageInstalled
2. **Banner**: Change 1.10.2, 1.10.3 from manual to FileContent
3. **Cron**: Change 6.5.x from manual to FilePermissions
4. **Files**: Add world-writable file checks
5. **Umask**: Add umask configuration checks

This alone will get us from **196 → 216 automated controls** and close the gap significantly!