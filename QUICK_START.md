# Quick Start Guide

## 🚀 Run Scanner (5 seconds)

```bash
cd Linux-CIS-Audit-code/rhel-8
sudo ./scan.sh
```

## 📊 View Report

```bash
# HTML (recommended)
firefox reports/vijenex-cis-report.html

# Or copy to local machine
scp user@server:~/Linux-CIS-Audit-code/rhel-8/reports/vijenex-cis-report.html .
```

## 🔍 Compare with OpenSCAP

```bash
# Run OpenSCAP
sudo oscap xccdf eval --profile xccdf_org.ssgproject.content_profile_cis \
  --results openscap-results.xml \
  --report openscap-report.html \
  /usr/share/xml/scap/ssg/content/ssg-rhel8-ds.xml

# Compare
# - Check PASS/FAIL counts
# - Look for mismatches
# - Share results with me
```

## 📝 What to Share

After running both scanners, share:

1. **Vijenex Results**
   - Total PASS/FAIL/MANUAL counts
   - Any errors in console output
   - HTML report (if possible)

2. **OpenSCAP Results**
   - Total PASS/FAIL counts
   - HTML report (if possible)

3. **Specific Mismatches**
   - Controls where Vijenex PASS but OpenSCAP FAIL
   - Controls where Vijenex FAIL but OpenSCAP PASS
   - Control IDs and descriptions

## 🐛 If Scanner Fails

```bash
# Check Python version (need 3.6+)
python3 --version

# Check if running as root
whoami

# Check milestone files exist
ls -la ../milestones/

# Run with verbose output
sudo python3 vijenex-cis.py --profile Level1 2>&1 | tee scan.log
```

## 📞 Report Issues

Share:
- Error messages
- System info: `cat /etc/os-release`
- Python version: `python3 --version`
- Log file: `scan.log`

---

**That's it! Run the scanner and share results for accuracy validation.**
