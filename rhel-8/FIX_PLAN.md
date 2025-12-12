# RHEL 8 Scanner - Complete Fix Plan

## Executive Summary

**Problem:** Scanner only implements 28% of controls (73/256). 191 controls marked as MANUAL should be automated.

**Solution:** Implement 10 missing control types + enhance HTML report

**Timeline:** 2 weeks for production-ready release

---

## Phase 1: Critical Control Types (Days 1-3)

### 1. SysctlParameter Control Type
**Purpose:** Check kernel parameters (network security, etc.)

**Implementation:**
```python
def check_sysctl_parameter(self, parameter: str, expected_value: str) -> Dict[str, Any]:
    """Check sysctl parameter value"""
    try:
        # Check running value
        stdout, stderr, returncode = self._run_command(f"sysctl {parameter}")
        
        # Check persistent config
        config_files = ['/etc/sysctl.conf', '/etc/sysctl.d/*.conf']
        
        # Compare values
        # Return PASS/FAIL
    except Exception as e:
        return error_result
```

**Controls Fixed:** 11 network security controls

---

### 2. FilePermissions Control Type
**Purpose:** Verify file/directory permissions, ownership

**Implementation:**
```python
def check_file_permissions(self, file_path: str, expected_perms: str, 
                          expected_owner: str, expected_group: str) -> Dict[str, Any]:
    """Check file permissions and ownership"""
    try:
        stat_info = os.stat(file_path)
        actual_perms = oct(stat_info.st_mode)[-4:]
        actual_owner = pwd.getpwuid(stat_info.st_uid).pw_name
        actual_group = grp.getgrgid(stat_info.st_gid).gr_name
        
        # Compare and return PASS/FAIL
    except Exception as e:
        return error_result
```

**Controls Fixed:** 9 file permission controls

---

### 3. SSHConfig Control Type
**Purpose:** Validate SSH daemon configuration

**Implementation:**
```python
def check_ssh_config(self, parameter: str, expected_value: str, 
                     comparison: str = "equals") -> Dict[str, Any]:
    """Check SSH configuration parameter"""
    try:
        # Use sshd -T to get effective config
        stdout, stderr, returncode = self._run_command("sshd -T")
        
        # Parse output for parameter
        # Compare with expected value
        # Support: equals, contains, regex, range
        
        # Return PASS/FAIL with actual value
    except Exception as e:
        return error_result
```

**Controls Fixed:** 17 SSH security controls

---

### 4. PAMConfig Control Type
**Purpose:** Validate PAM (password/authentication) configuration

**Implementation:**
```python
def check_pam_config(self, pam_file: str, module: str, 
                     parameter: str, expected_value: str) -> Dict[str, Any]:
    """Check PAM configuration"""
    try:
        pam_path = f"/etc/pam.d/{pam_file}"
        
        # Read PAM file
        # Find module line
        # Extract parameter value
        # Compare with expected
        
        # Return PASS/FAIL
    except Exception as e:
        return error_result
```

**Controls Fixed:** 12 password policy controls

---

### 5. FileContent Control Type
**Purpose:** Check configuration file content (grep-style)

**Implementation:**
```python
def check_file_content(self, file_path: str, pattern: str, 
                       match_type: str = "contains") -> Dict[str, Any]:
    """Check file content for pattern"""
    try:
        # Read file
        # Search for pattern (regex, exact, contains)
        # Return PASS if found, FAIL if not
        
        # Support multiple files (glob patterns)
    except Exception as e:
        return error_result
```

**Controls Fixed:** 20+ configuration validation controls

---

## Phase 2: Advanced Control Types (Days 4-7)

### 6. AuditRules Control Type
**Purpose:** Validate auditd rules

**Implementation:**
```python
def check_audit_rule(self, rule_pattern: str, rule_type: str = "syscall") -> Dict[str, Any]:
    """Check audit rule exists"""
    try:
        # Check running rules: auditctl -l
        # Check persistent rules: /etc/audit/rules.d/*.rules
        # Match pattern
        # Return PASS/FAIL
    except Exception as e:
        return error_result
```

**Controls Fixed:** 60+ audit logging controls

---

### 7. UserConfig Control Type
**Purpose:** Validate user account settings

**Implementation:**
```python
def check_user_config(self, check_type: str, **params) -> Dict[str, Any]:
    """Check user configuration"""
    # Types: password_expiry, uid_unique, home_dir_perms, etc.
    try:
        if check_type == "password_expiry":
            # Check /etc/shadow
        elif check_type == "uid_unique":
            # Check /etc/passwd for duplicate UIDs
        # etc.
    except Exception as e:
        return error_result
```

**Controls Fixed:** 15+ user account controls

---

### 8. GrubConfig Control Type
**Purpose:** Validate bootloader configuration

**Implementation:**
```python
def check_grub_config(self, parameter: str, expected_value: str) -> Dict[str, Any]:
    """Check GRUB configuration"""
    try:
        # Use grubby --info=ALL
        # Check /etc/default/grub
        # Validate parameter
    except Exception as e:
        return error_result
```

**Controls Fixed:** 5+ boot security controls

---

### 9. SELinuxConfig Control Type
**Purpose:** Validate SELinux configuration

**Implementation:**
```python
def check_selinux_config(self, check_type: str, expected_value: str) -> Dict[str, Any]:
    """Check SELinux configuration"""
    try:
        if check_type == "mode":
            # getenforce
        elif check_type == "policy":
            # sestatus
        elif check_type == "config":
            # /etc/selinux/config
    except Exception as e:
        return error_result
```

**Controls Fixed:** 8+ SELinux controls

---

### 10. CronPermissions Control Type
**Purpose:** Validate cron file permissions

**Implementation:**
```python
def check_cron_permissions(self, cron_path: str, expected_perms: str) -> Dict[str, Any]:
    """Check cron file/directory permissions"""
    # Similar to FilePermissions but cron-specific
    # Check: /etc/crontab, /etc/cron.d/, /etc/cron.{hourly,daily,weekly,monthly}
```

**Controls Fixed:** 8+ cron security controls

---

## Phase 3: HTML Report Enhancement (Days 8-10)

### Current HTML Issues:
1. ❌ No detailed descriptions
2. ❌ No remediation commands
3. ❌ No severity ratings
4. ❌ No evidence/proof
5. ❌ Basic styling
6. ❌ No charts/graphs
7. ❌ No section breakdown

### Enhanced HTML Features:

#### 1. Executive Summary Section
```html
<div class="executive-summary">
    <h2>Executive Summary</h2>
    <div class="compliance-score">
        <div class="score-circle">76%</div>
        <p>Overall Compliance</p>
    </div>
    <div class="severity-breakdown">
        <h3>Failures by Severity</h3>
        <ul>
            <li>Critical: 0</li>
            <li>High: 5</li>
            <li>Medium: 91</li>
            <li>Low: 8</li>
        </ul>
    </div>
</div>
```

#### 2. Section Breakdown
```html
<div class="section-summary">
    <h3>Compliance by Section</h3>
    <table>
        <tr>
            <th>Section</th>
            <th>Pass</th>
            <th>Fail</th>
            <th>Compliance %</th>
        </tr>
        <tr>
            <td>1. Initial Setup</td>
            <td>45</td>
            <td>12</td>
            <td>78.9%</td>
        </tr>
        <!-- More sections -->
    </table>
</div>
```

#### 3. Detailed Control Information
```html
<div class="control-detail">
    <h4>5.1.6 - Ensure SSH Root Login is Disabled</h4>
    <div class="control-info">
        <span class="severity high">HIGH</span>
        <span class="status fail">FAIL</span>
    </div>
    <div class="description">
        <h5>Description:</h5>
        <p>The PermitRootLogin parameter specifies if the root user can log in using ssh. 
           Disallowing root logins over SSH requires system admins to authenticate using 
           their own individual account, then escalating to root via sudo or su.</p>
    </div>
    <div class="rationale">
        <h5>Rationale:</h5>
        <p>Disallowing root logins over SSH provides an additional layer of accountability 
           and security. When root logins are disabled, all access is logged with the 
           actual user account name.</p>
    </div>
    <div class="current-value">
        <h5>Current Value:</h5>
        <code>PermitRootLogin yes</code>
    </div>
    <div class="expected-value">
        <h5>Expected Value:</h5>
        <code>PermitRootLogin no</code>
    </div>
    <div class="evidence">
        <h5>Evidence Command:</h5>
        <code>sshd -T | grep permitrootlogin</code>
    </div>
    <div class="remediation">
        <h5>Remediation:</h5>
        <pre>
# Edit /etc/ssh/sshd_config
sed -i 's/^PermitRootLogin.*/PermitRootLogin no/' /etc/ssh/sshd_config

# Restart SSH service
systemctl restart sshd
        </pre>
    </div>
    <div class="impact">
        <h5>Impact:</h5>
        <p>Root users will need to login with their individual accounts and use sudo/su 
           to gain root privileges.</p>
    </div>
</div>
```

#### 4. Modern Styling
```css
/* Professional color scheme */
:root {
    --primary: #c00;
    --success: #28a745;
    --warning: #ffc107;
    --danger: #dc3545;
    --info: #17a2b8;
}

/* Responsive design */
@media (max-width: 768px) {
    /* Mobile-friendly layout */
}

/* Print-friendly */
@media print {
    /* Optimized for PDF export */
}
```

#### 5. Interactive Features
```javascript
// Filter controls by status
function filterByStatus(status) { }

// Search controls
function searchControls(query) { }

// Export to PDF
function exportToPDF() { }

// Expand/collapse sections
function toggleSection(sectionId) { }
```

---

## Phase 4: Testing & Validation (Days 11-12)

### Test Matrix:

| Test Case | Description | Expected Result |
|-----------|-------------|-----------------|
| Clean RHEL 8.5 | Fresh install | Baseline failures |
| Hardened RHEL 8.5 | CIS-compliant | All pass |
| RHEL 8.0 | Older version | Compatible |
| RHEL 8.10 | Latest version | Compatible |
| Without root | Non-root user | Graceful degradation |
| Network issues | Offline system | No crashes |
| Large audit logs | 10GB+ logs | Performance OK |

### Validation Checklist:
- [ ] All 256+ controls execute without errors
- [ ] No false positives on baseline system
- [ ] No false negatives on hardened system
- [ ] Scan completes in < 5 minutes
- [ ] HTML report renders correctly
- [ ] CSV export works
- [ ] All remediation commands are valid
- [ ] Documentation is complete

---

## Phase 5: Documentation (Days 13-14)

### Required Documentation:

1. **README.md**
   - Installation instructions
   - Usage examples
   - Command-line options
   - Output formats

2. **COMPARISON.md**
   - Vijenex vs OpenSCAP feature comparison
   - Performance benchmarks
   - Advantages of Vijenex

3. **CONTROLS.md**
   - Complete list of all controls
   - Control types and their usage
   - Adding custom controls

4. **REMEDIATION_GUIDE.md**
   - Step-by-step remediation for common failures
   - Automation scripts
   - Best practices

5. **FAQ.md**
   - Common questions
   - Troubleshooting
   - Support information

---

## Success Metrics

### Before Release:
- [ ] 256+ automated controls (currently 73)
- [ ] 0 manual controls for automatable checks (currently 191)
- [ ] Detailed HTML report with all sections
- [ ] All SSH controls automated (17/17)
- [ ] All PAM controls automated (12/12)
- [ ] All Audit controls automated (60+/60+)
- [ ] All Sysctl controls automated (20+/20+)
- [ ] Scan time < 5 minutes
- [ ] Zero crashes on test systems
- [ ] Complete documentation

### Competitive Advantages Over OpenSCAP:
1. ✅ Faster scan time (< 5 min vs 10+ min)
2. ✅ Better HTML report (detailed vs basic)
3. ✅ Easier to use (single command vs complex)
4. ✅ Better remediation guidance
5. ✅ Modern UI/UX
6. ✅ Active development and support
7. ✅ Open source and free

---

## Resource Requirements

### Development:
- 1 developer, full-time
- 2 weeks (80 hours)

### Testing:
- 3-4 RHEL 8 test systems
- Various configurations (clean, hardened, minimal)

### Tools:
- Python 3.6+
- RHEL 8 CIS Benchmark v4.0.0 PDF
- OpenSCAP for comparison testing

---

## Risk Mitigation

### Risks:
1. **Timeline slippage** - Complex controls take longer
   - Mitigation: Prioritize critical controls first

2. **False positives** - Incorrect FAIL results
   - Mitigation: Extensive testing on multiple systems

3. **Performance issues** - Slow scans
   - Mitigation: Optimize slow controls, parallel execution

4. **Compatibility issues** - Different RHEL versions
   - Mitigation: Test on RHEL 8.0 through 8.10

---

## Next Steps

### Immediate (Today):
1. Review and approve this plan
2. Set up development environment
3. Start implementing SysctlParameter control type

### This Week:
4. Complete Phase 1 (5 critical control types)
5. Update all milestone files
6. Test on production system

### Next Week:
7. Complete Phase 2 (advanced control types)
8. Enhance HTML report
9. Complete testing and documentation

### Week 3:
10. Final testing and validation
11. Release v1.0.0
12. Marketing and announcement

---

## Conclusion

**Current State:** Prototype with 28% functionality
**Target State:** Production-ready with 100% functionality
**Timeline:** 2 weeks
**Outcome:** Better than OpenSCAP

**Let's build this properly and release something we're proud of!** 🚀
