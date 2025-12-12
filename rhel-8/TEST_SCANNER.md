# RHEL 8 CIS Scanner - Testing Guide

## Scanner Status ✅

**Total Controls Implemented: 58**

### Milestone Breakdown:
- ✅ Milestone 1.1: Filesystem - Kernel Modules & /tmp (15 controls)
- ✅ Milestone 1.2: Filesystem - Partitions (22 controls)  
- ✅ Milestone 1.3: Package Management & AIDE (6 controls)
- ✅ Milestone 1.4: Secure Boot & Process Hardening (7 controls)
- ✅ Milestone 1.5: SELinux Configuration (8 controls)

## How to Test on RHEL 8 Machine

### 1. Copy Scanner to RHEL 8 System
```bash
# From your Mac, copy the entire rhel-8 directory to your RHEL 8 machine
scp -r /Users/satish.korra/Desktop/Linux-CIS-Audit-code/rhel-8 user@rhel8-machine:/tmp/
```

### 2. Run Scanner on RHEL 8
```bash
# SSH to your RHEL 8 machine
ssh user@rhel8-machine

# Navigate to scanner directory
cd /tmp/rhel-8/scripts

# Run scanner with sudo (required for system checks)
sudo python3 vijenex-cis.py

# Or specify output directory
sudo python3 vijenex-cis.py --output-dir /tmp/reports

# Run specific milestones only
sudo python3 vijenex-cis.py --milestones milestone-1-1.json milestone-1-2.json

# Run Level 2 profile
sudo python3 vijenex-cis.py --profile Level2
```

### 3. View Reports
```bash
# Reports are generated in ../reports/ directory
ls -lh ../reports/

# View CSV report
cat ../reports/vijenex-cis-results.csv

# Open HTML report (copy to your Mac to view in browser)
scp user@rhel8-machine:/tmp/rhel-8/reports/vijenex-cis-report.html ~/Desktop/
```

## Expected Output

### Terminal Output:
```
=============================================================
                        VIJENEX                              
      Red Hat Enterprise Linux 8 CIS Scanner           
           Powered by Vijenex Security Platform             
        https://github.com/vijenex/linux-cis-scanner        
=============================================================

🔍 Starting CIS Compliance Scan...
📋 Profile: Level1
🐧 Distribution: Red Hat Enterprise Linux 8.5
📁 Milestones: 5
────────────────────────────────────────────────────────────
📄 Processing milestone-1-1.json...
  ✓ 1.1.1.1: Ensure cramfs kernel module is not available...
  ✓ 1.1.1.2: Ensure freevxfs kernel module is not available...
  ...
────────────────────────────────────────────────────────────

=============================================================
                    SCAN COMPLETED                           
=============================================================
Total Checks: 58
Passed: XX
Failed: XX
Manual: XX
Success Rate: XX%
=============================================================

📊 Generating reports...
📄 HTML report: /tmp/rhel-8/reports/vijenex-cis-report.html
📊 CSV report: /tmp/rhel-8/reports/vijenex-cis-results.csv

🎉 Vijenex CIS scan completed successfully!
```

### CSV Report Format (7 columns):
```
Id,Title,Section,Status,CISReference,Remediation,Description
1.1.1.1,Ensure cramfs kernel module is not available,1.1 Filesystem Configuration,PASS,CIS RHEL 8 v4.0.0 - 1.1.1.1,Create /etc/modprobe.d/cramfs.conf with install cramfs /bin/false,Module cramfs: blacklisted=True loaded=False
```

## Architecture

### JSON Milestone Files (WHAT to check):
```json
{
  "milestone": "1.1",
  "controls": [
    {
      "id": "1.1.1.1",
      "title": "Ensure cramfs kernel module is not available",
      "type": "KernelModule",
      "module_name": "cramfs",
      "expected_status": "not_available"
    }
  ]
}
```

### Python Scanner (HOW to check):
- Reads JSON milestone files
- Executes Linux commands: `lsmod`, `modprobe`, `findmnt`, `grep`, `rpm`
- Generates CSV/HTML reports
- 7-column output format

## Troubleshooting

### Permission Denied
```bash
# Scanner needs root access for system checks
sudo python3 vijenex-cis.py
```

### Python Not Found
```bash
# Install Python 3 if missing
sudo dnf install python3
```

### Module Not Found
```bash
# Ensure you're in the scripts directory
cd /tmp/rhel-8/scripts
python3 vijenex-cis.py
```

## Next Steps

After testing the current 58 controls, we can rapidly build:
- Milestone 2.1: Services - Special Purpose (15+ controls)
- Milestone 2.2: Services - Client Services (10+ controls)
- Milestone 3.x: Network Configuration (40+ controls)
- Milestone 4.x: Logging & Auditing (50+ controls)
- Milestone 5.x: Access Control (80+ controls)
- Milestone 6.x: System Maintenance (60+ controls)

**Target: 350+ total controls covering full CIS RHEL 8 v4.0.0 Benchmark**
