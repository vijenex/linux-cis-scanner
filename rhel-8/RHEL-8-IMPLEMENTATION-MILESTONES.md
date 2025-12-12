# RHEL 8 CIS Scanner Implementation Milestones
## CIS Red Hat Enterprise Linux 8 Benchmark v4.0.0

**Target System:** RHEL 8.5 (Ootpa)  
**Scanner Architecture:** Python-based (following Ubuntu 22.04/24.04 pattern)  
**Output Format:** 7-column CSV (Phase 1 improvements included)  
**Estimated Total Controls:** ~350+ controls

---

## Milestone 1: Project Setup & Core Framework
**Estimated Controls:** 0 (Infrastructure)

### Tasks:
1. Create project structure:
   - `/rhel-8/scripts/vijenex-cis.py` (main scanner)
   - `/rhel-8/reports/` (output directory)
   - `/rhel-8/README.md` (documentation)

2. Implement core scanner framework:
   - Scanner signature (simple box design with RHEL 8 branding)
   - Result structure: `actual_value`, `evidence_command`, `description`
   - CSV writer (7 columns: Id, Title, Section, Status, CISReference, Remediation, Description)
   - HTML report generator
   - Summary display with success rate calculation

3. System detection:
   - Verify RHEL 8.x detection from `/etc/os-release`
   - Version compatibility check

**Deliverable:** Working scanner framework with no controls

---

## Milestone 2: Section 1.1 - Filesystem Configuration
**Estimated Controls:** ~20 controls

### 1.1.1 Configure Filesystem Kernel Modules (10 controls)
- 1.1.1.1: Ensure cramfs kernel module is not available
- 1.1.1.2: Ensure freevxfs kernel module is not available
- 1.1.1.3: Ensure hfs kernel module is not available
- 1.1.1.4: Ensure hfsplus kernel module is not available
- 1.1.1.5: Ensure jffs2 kernel module is not available
- 1.1.1.6: Ensure overlay kernel module is not available (Level 2)
- 1.1.1.7: Ensure squashfs kernel module is not available (Level 2)
- 1.1.1.8: Ensure udf kernel module is not available (Level 2)
- 1.1.1.9: Ensure firewire-core kernel module is not available
- 1.1.1.10: Ensure usb-storage kernel module is not available
- 1.1.1.11: Ensure unused filesystems kernel modules are not available (Manual)

### 1.1.2 Configure Filesystem Partitions (~10 controls)
- 1.1.2.1.x: /tmp partition configuration (4 controls)
- 1.1.2.2.x: /dev/shm partition configuration (4 controls)
- 1.1.2.3.x: /home partition configuration (3 controls)
- 1.1.2.4.x: /var partition configuration (3 controls)
- 1.1.2.5.x: /var/tmp partition configuration (4 controls)
- 1.1.2.6.x: /var/log partition configuration (4 controls)
- 1.1.2.7.x: /var/log/audit partition configuration (4 controls)

**Key Commands:**
- `lsmod`, `modprobe --showconfig`
- `findmnt -kn <partition>`
- `systemctl is-enabled tmp.mount`

**Deliverable:** Filesystem security controls implemented

---

## Milestone 3: Section 1.2 - Package Management
**Estimated Controls:** ~6 controls

### 1.2.1 Configure Package Repositories (5 controls)
- 1.2.1.1: Ensure GPG keys are configured (Manual)
- 1.2.1.2: Ensure gpgcheck is configured
- 1.2.1.3: Ensure repo_gpgcheck is globally activated (Manual, Level 2)
- 1.2.1.4: Ensure package manager repositories are configured (Manual)
- 1.2.1.5: Ensure weak dependencies are configured (Level 2)

### 1.2.2 Configure Package Updates (1 control)
- 1.2.2.1: Ensure updates, patches, and additional security software are installed (Manual)

**Key Commands:**
- `rpm -q gpg-pubkey`, `grep gpgkey /etc/yum.repos.d/*`
- `grep gpgcheck /etc/dnf/dnf.conf`
- `dnf check-update`, `dnf needs-restarting -r`

**Deliverable:** Package management security controls

---

## Milestone 4: Section 1.3 - Mandatory Access Control (SELinux)
**Estimated Controls:** ~8 controls

### 1.3.1 Configure SELinux (8+ controls)
- 1.3.1.1: Ensure SELinux is installed
- 1.3.1.2: Ensure SELinux is not disabled in bootloader configuration
- 1.3.1.3: Ensure SELinux policy is configured
- 1.3.1.4: Ensure the SELinux mode is not disabled
- Additional SELinux state and configuration controls

**Key Commands:**
- `rpm -q libselinux`
- `grubby --info=ALL`
- `grep SELINUX /etc/selinux/config`
- `getenforce`, `sestatus`

**Deliverable:** SELinux security controls

---

## Milestone 5: Section 2 - Services Configuration
**Estimated Controls:** ~30-40 controls

### Expected Subsections:
- 2.1: Configure Time Synchronization
- 2.2: Configure Special Purpose Services
- 2.3: Configure Service Clients
- 2.4: Ensure unnecessary services are removed

**Key Services to Check:**
- chrony/ntp (time sync)
- X Window System
- Avahi, CUPS, DHCP, DNS, FTP, HTTP, IMAP/POP3, Samba, SNMP, rsync, NIS

**Key Commands:**
- `systemctl is-enabled <service>`
- `systemctl status <service>`
- `rpm -q <package>`

**Deliverable:** Services security controls

---

## Milestone 6: Section 3 - Network Configuration
**Estimated Controls:** ~40-50 controls

### Expected Subsections:
- 3.1: Disable unused network protocols and devices
- 3.2: Network Parameters (Host Only)
- 3.3: Network Parameters (Host and Router)
- 3.4: Uncommon Network Protocols
- 3.5: Firewall Configuration (firewalld/nftables/iptables)

**Key Commands:**
- `sysctl <parameter>`
- `grep <parameter> /etc/sysctl.conf /etc/sysctl.d/*`
- `firewall-cmd --list-all`
- `nft list ruleset`

**Deliverable:** Network security controls

---

## Milestone 7: Section 4 - Logging and Auditing
**Estimated Controls:** ~60-80 controls

### Expected Subsections:
- 4.1: Configure System Accounting (auditd)
  - auditd configuration
  - Audit rules for file access, system calls, privileged commands
  - Audit log configuration
- 4.2: Configure Logging (rsyslog/journald)
  - rsyslog configuration
  - journald configuration
  - Log file permissions

**Key Commands:**
- `systemctl is-enabled auditd`
- `auditctl -l`
- `grep <rule> /etc/audit/rules.d/*.rules`
- `systemctl is-enabled rsyslog`
- `grep <config> /etc/rsyslog.conf /etc/rsyslog.d/*`

**Deliverable:** Logging and auditing controls (largest section)

---

## Milestone 8: Section 5 - Access, Authentication and Authorization
**Estimated Controls:** ~80-100 controls

### Expected Subsections:
- 5.1: Configure time-based job schedulers (cron, at)
- 5.2: Configure SSH Server
- 5.3: Configure privilege escalation (sudo, su)
- 5.4: Configure PAM
- 5.5: User Accounts and Environment
  - Password policies
  - Account lockout
  - User shell timeout
  - Default umask

**Key Commands:**
- `stat /etc/crontab`, `ls -l /etc/cron.*`
- `sshd -T`, `grep <param> /etc/ssh/sshd_config`
- `grep <param> /etc/sudoers /etc/sudoers.d/*`
- `grep <param> /etc/pam.d/*`
- `grep <param> /etc/login.defs /etc/security/pwquality.conf`

**Deliverable:** Access control and authentication controls (largest section)

---

## Milestone 9: Section 6 - System Maintenance
**Estimated Controls:** ~30-40 controls

### Expected Subsections:
- 6.1: System File Permissions
  - /etc/passwd, /etc/shadow, /etc/group permissions
  - World writable files
  - Unowned files
  - SUID/SGID files
- 6.2: User and Group Settings
  - Duplicate UIDs/GIDs
  - Reserved UIDs
  - Root PATH integrity
  - User home directories

**Key Commands:**
- `stat /etc/passwd /etc/shadow /etc/group`
- `find / -xdev -type f -perm -002`
- `find / -xdev -nouser -o -nogroup`
- `find / -xdev -type f -perm -4000 -o -perm -2000`
- `awk -F: '{print $1":"$3}' /etc/passwd | sort`

**Deliverable:** System maintenance controls

---

## Milestone 10: Testing, Validation & Documentation
**Estimated Controls:** All (~350+)

### Tasks:
1. **End-to-End Testing:**
   - Test on clean RHEL 8.5 system
   - Test on hardened RHEL 8.5 system
   - Verify all controls execute without errors
   - Validate CSV output format
   - Validate HTML report generation

2. **Performance Testing:**
   - Measure scan time
   - Optimize slow controls
   - Test with large audit logs

3. **Documentation:**
   - Update README.md with usage instructions
   - Document dependencies (Python version, required packages)
   - Create CHANGES-v1.0.0.md changelog
   - Add troubleshooting guide

4. **Code Quality:**
   - Code review
   - Error handling validation
   - Logging improvements

**Deliverable:** Production-ready RHEL 8 CIS scanner v1.0.0

---

## Implementation Notes

### Control Complexity Levels:
- **Automated:** Can be fully automated with commands
- **Manual:** Requires human review/judgment
- **Level 1:** Basic security (all systems)
- **Level 2:** Enhanced security (high-security environments)

### Common Audit Patterns:
1. **File/Directory Checks:** `stat`, `ls -l`, `find`
2. **Package Checks:** `rpm -q <package>`
3. **Service Checks:** `systemctl is-enabled`, `systemctl status`
4. **Configuration Checks:** `grep`, `awk`, `sed`
5. **Kernel Parameters:** `sysctl`, `grep /proc/sys/`
6. **Module Checks:** `lsmod`, `modprobe --showconfig`
7. **Firewall Checks:** `firewall-cmd`, `nft`, `iptables`
8. **Audit Rules:** `auditctl -l`, `grep /etc/audit/rules.d/`

### Scanner Architecture (Following Ubuntu Pattern):
```python
# Core structure
class CISControl:
    def __init__(self, id, title, section, level, automation):
        self.id = id
        self.title = title
        self.section = section
        self.level = level  # 1 or 2
        self.automation = automation  # Automated or Manual
        
    def audit(self):
        # Return: status, actual_value, evidence_command, description
        pass

# Result structure
result = {
    'id': '1.1.1.1',
    'title': 'Ensure cramfs kernel module is not available',
    'section': '1.1 Filesystem',
    'status': 'PASS' or 'FAIL',
    'cis_reference': 'Level 1 - Server, Level 1 - Workstation',
    'remediation': '<remediation steps>',
    'description': '<description>',
    'actual_value': '<what was found>',
    'evidence_command': '<command used>',
}
```

### CSV Output Format (7 columns):
```
Id,Title,Section,Status,CISReference,Remediation,Description
1.1.1.1,Ensure cramfs kernel module is not available,1.1 Filesystem,PASS,Level 1 - Server | Level 1 - Workstation,<remediation>,<description>
```

---

## Estimated Timeline

| Milestone | Controls | Estimated Time |
|-----------|----------|----------------|
| M1: Framework | 0 | 2-3 hours |
| M2: Filesystem | ~20 | 4-6 hours |
| M3: Package Mgmt | ~6 | 2-3 hours |
| M4: SELinux | ~8 | 2-3 hours |
| M5: Services | ~35 | 6-8 hours |
| M6: Network | ~45 | 8-10 hours |
| M7: Logging/Audit | ~70 | 12-15 hours |
| M8: Access/Auth | ~90 | 15-20 hours |
| M9: System Maint | ~35 | 6-8 hours |
| M10: Testing/Docs | All | 4-6 hours |
| **TOTAL** | **~350** | **60-80 hours** |

---

## Success Criteria

1. ✅ All automated controls implemented and tested
2. ✅ Manual controls identified with clear instructions
3. ✅ CSV output matches 7-column format
4. ✅ HTML report generated successfully
5. ✅ Scanner completes in < 5 minutes on standard system
6. ✅ No false positives on baseline RHEL 8.5 system
7. ✅ Comprehensive documentation provided
8. ✅ Error handling for missing commands/files
9. ✅ Compatible with RHEL 8.0 through 8.x

---

## Next Steps

1. **Review this milestone plan** - Confirm approach and timeline
2. **Start Milestone 1** - Build core framework
3. **Iterative development** - Complete one milestone at a time
4. **Regular testing** - Test after each milestone
5. **Documentation** - Update docs as we progress

**Ready to start building?** Let's begin with Milestone 1: Project Setup & Core Framework! 🚀
