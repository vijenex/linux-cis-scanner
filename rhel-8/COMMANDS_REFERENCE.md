# RHEL 8 CIS Scanner - Command Reference

## ✅ Same Commands as Ubuntu Scanner

The RHEL 8 scanner follows the **exact same command structure** as the Ubuntu scanner documented in the GitHub README.

---

## 📋 Standard Commands

### Basic Scan
```bash
cd /path/to/rhel-8/scripts
sudo python3 vijenex-cis.py
```

### Profile Selection
```bash
# Level 1 (default)
sudo python3 vijenex-cis.py --profile Level1

# Level 2 (stricter)
sudo python3 vijenex-cis.py --profile Level2
```

### Custom Output Directory
```bash
sudo python3 vijenex-cis.py --output-dir /tmp/my-reports
sudo python3 vijenex-cis.py --output-dir /var/log/audit
```

### Report Format Selection
```bash
# Both HTML and CSV (default)
sudo python3 vijenex-cis.py --format both

# HTML only
sudo python3 vijenex-cis.py --format html

# CSV only
sudo python3 vijenex-cis.py --format csv
```

### Specific Milestones
```bash
# Single milestone
sudo python3 vijenex-cis.py --milestones milestone-1-1.json

# Multiple milestones
sudo python3 vijenex-cis.py --milestones milestone-1-1.json milestone-1-2.json milestone-1-5.json

# All milestones (default)
sudo python3 vijenex-cis.py
```

### Combined Options
```bash
# Level 2 profile with custom output and HTML only
sudo python3 vijenex-cis.py --profile Level2 --output-dir /tmp/reports --format html

# Specific milestones with CSV output
sudo python3 vijenex-cis.py --milestones milestone-1-1.json milestone-1-5.json --format csv
```

---

## 📊 Parameters Reference

| Parameter | Description | Default | Example |
|-----------|-------------|---------|---------|
| `--output-dir` | Report output directory | `../reports` | `--output-dir /var/log/audit` |
| `--profile` | CIS profile level | `Level1` | `--profile Level2` |
| `--format` | Report format | `both` | `--format html` or `--format csv` |
| `--milestones` | Specific milestone files | All files | `--milestones milestone-1-1.json` |

---

## 🎯 Example Workflows

### Quick Security Check
```bash
cd /tmp/rhel-8/scripts
sudo python3 vijenex-cis.py --format html --output-dir /tmp/quick-scan
```

### Full Compliance Audit
```bash
cd /tmp/rhel-8/scripts
sudo python3 vijenex-cis.py --profile Level2 --format both
```

### Filesystem Only Check
```bash
cd /tmp/rhel-8/scripts
sudo python3 vijenex-cis.py --milestones milestone-1-1.json milestone-1-2.json
```

### SELinux Configuration Check
```bash
cd /tmp/rhel-8/scripts
sudo python3 vijenex-cis.py --milestones milestone-1-5.json --format csv
```

---

## 📁 Output Files

After running the scanner, reports are generated in the output directory:

```
reports/
├── vijenex-cis-results.csv      # Detailed CSV report
└── vijenex-cis-report.html      # HTML report with charts
```

### CSV Format (7 columns):
```
Id,Title,Section,Status,CISReference,Remediation,Description
1.1.1.1,Ensure cramfs kernel module is not available,1.1 Filesystem,PASS,CIS RHEL 8 v4.0.0 - 1.1.1.1,Create /etc/modprobe.d/cramfs.conf,Module blacklisted
```

---

## 🚀 Quick Test on RHEL 8 Machine

```bash
# 1. Copy scanner to RHEL 8
scp -r /Users/satish.korra/Desktop/Linux-CIS-Audit-code/rhel-8 user@rhel8-machine:/tmp/

# 2. SSH and run
ssh user@rhel8-machine
cd /tmp/rhel-8/scripts
sudo python3 vijenex-cis.py

# 3. View results
cat ../reports/vijenex-cis-results.csv
```

---

## ✅ Consistency with Ubuntu Scanner

The RHEL 8 scanner uses:
- ✅ Same command-line arguments
- ✅ Same parameter names
- ✅ Same output format (7-column CSV)
- ✅ Same report names
- ✅ Same JSON milestone architecture
- ✅ Same Python execution engine

**You can use the exact same commands documented in the GitHub README!**
