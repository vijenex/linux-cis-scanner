# Scanner Test Checklist - MUST RUN BEFORE DEPLOYMENT

**Date**: December 13, 2024  
**Version**: Latest (commit ae63ba8)

---

## ✅ Fixes Applied

1. **Mount Options** - Return SKIPPED (not FAIL) when partition doesn't exist
2. **SELinux** - Fixed package name from 'aide' to 'libselinux'
3. **Service Checks** - Improved to check both is-enabled and is-active

---

## 🔍 MANDATORY TESTS ON RHEL 8 SERVER

### Step 1: Deploy Latest Binary

```bash
# Copy latest binary
scp vijenex-cis-amd64 user@rhel8-server:/tmp/

# Install
ssh user@rhel8-server
sudo mv /tmp/vijenex-cis-amd64 /usr/local/bin/vijenex-cis
sudo chmod +x /usr/local/bin/vijenex-cis
```

### Step 2: Run Fresh Scan

```bash
# Run scan
sudo vijenex-cis --profile Level1 --output-dir /tmp/vijenex-test

# Check output
ls -lh /tmp/vijenex-test/
```

### Step 3: Verify CSV Output

```bash
# Check CSV structure
head -5 /tmp/vijenex-test/vijenex-cis-results.csv

# Count results
echo "PASS: $(grep -c ',PASS,' /tmp/vijenex-test/vijenex-cis-results.csv)"
echo "FAIL: $(grep -c ',FAIL,' /tmp/vijenex-test/vijenex-cis-results.csv)"
echo "MANUAL: $(grep -c ',MANUAL,' /tmp/vijenex-test/vijenex-cis-results.csv)"
echo "SKIPPED: $(grep -c ',SKIPPED,' /tmp/vijenex-test/vijenex-cis-results.csv)"

# Check for broken lines (should be 0)
awk -F',' 'NF!=7 {print NR": "$0}' /tmp/vijenex-test/vijenex-cis-results.csv
```

**Expected:**
- CSV has 7 columns: Id,Title,Section,Status,CISReference,Remediation,Description
- No broken lines
- All fields properly quoted if they contain commas/newlines

### Step 4: Verify HTML Output

```bash
# Check HTML file
ls -lh /tmp/vijenex-test/vijenex-cis-report.html

# Check for JavaScript
grep -c "toggleDetails" /tmp/vijenex-test/vijenex-cis-report.html

# Copy to local machine to view
scp user@rhel8-server:/tmp/vijenex-test/vijenex-cis-report.html .
```

**Manual Checks:**
- [ ] Open HTML in browser
- [ ] Click on controls - should expand/collapse
- [ ] Check Description field - should show CIS description (not overwritten)
- [ ] Check Title field - should be complete (not broken)
- [ ] Check all status badges show correctly

### Step 5: Verify Mount Option Fix

```bash
# Check which partitions exist
df -h
findmnt

# Check mount option results
grep "mount\|partition" /tmp/vijenex-test/vijenex-cis-results.csv | grep -E "FAIL|SKIPPED"
```

**Expected:**
- Controls for non-existent partitions should show SKIPPED (not FAIL)
- Example: If /home is not separate partition, "nodev on /home" should be SKIPPED
- Only controls for existing partitions should show FAIL if option missing

### Step 6: Verify SELinux Fix

```bash
# Check SELinux status
rpm -q libselinux
getenforce
sestatus

# Check scanner result
grep "1.3.1.1" /tmp/vijenex-test/vijenex-cis-results.csv
```

**Expected:**
- If libselinux is installed, control 1.3.1.1 should PASS
- If SELinux is enforcing, related controls should PASS

### Step 7: Run OpenSCAP for Comparison

```bash
# Install OpenSCAP
sudo dnf install -y openscap-scanner scap-security-guide

# Run OpenSCAP
sudo oscap xccdf eval \
  --profile xccdf_org.ssgproject.content_profile_cis_server_l1 \
  --results /tmp/openscap-results.xml \
  --report /tmp/openscap-report.html \
  /usr/share/xml/scap/ssg/content/ssg-rhel8-ds.xml

# Count results
grep -c 'result="pass"' /tmp/openscap-results.xml
grep -c 'result="fail"' /tmp/openscap-results.xml
```

### Step 8: Compare Results

```bash
# Create comparison
echo "=== COMPARISON ==="
echo "Vijenex:"
echo "  PASS: $(grep -c ',PASS,' /tmp/vijenex-test/vijenex-cis-results.csv)"
echo "  FAIL: $(grep -c ',FAIL,' /tmp/vijenex-test/vijenex-cis-results.csv)"
echo "  SKIP: $(grep -c ',SKIPPED,' /tmp/vijenex-test/vijenex-cis-results.csv)"
echo "  MANUAL: $(grep -c ',MANUAL,' /tmp/vijenex-test/vijenex-cis-results.csv)"
echo ""
echo "OpenSCAP:"
echo "  pass: $(grep -c 'result="pass"' /tmp/openscap-results.xml)"
echo "  fail: $(grep -c 'result="fail"' /tmp/openscap-results.xml)"
echo "  notapplicable: $(grep -c 'result="notapplicable"' /tmp/openscap-results.xml)"
```

**Expected:**
- Vijenex PASS + FAIL should be ~218 (Level 1 automated)
- OpenSCAP pass + fail should be ~256
- Vijenex SKIPPED should be ~30-50 (non-existent partitions)
- Failure counts should be similar (within 20)

### Step 9: Manual Verification of Sample Controls

#### Test 1: cramfs Module
```bash
# Check actual state
lsmod | grep cramfs
modprobe -n -v cramfs

# Check scanner result
grep "1.1.1.1" /tmp/vijenex-test/vijenex-cis-results.csv

# Check OpenSCAP result
grep -A 2 "cramfs" /tmp/openscap-report.html
```

**Verify:** Both scanners agree on result

#### Test 2: /tmp Mount Options
```bash
# Check actual state
mount | grep " /tmp "
findmnt /tmp

# Check scanner results
grep "1.1.2.1" /tmp/vijenex-test/vijenex-cis-results.csv

# If /tmp is NOT separate partition:
# - 1.1.2.1.1 should FAIL (no separate partition)
# - 1.1.2.1.2, 1.1.2.1.3, 1.1.2.1.4 should SKIPPED (partition doesn't exist)
```

**Verify:** SKIPPED for mount options when partition doesn't exist

#### Test 3: SELinux
```bash
# Check actual state
rpm -q libselinux
getenforce

# Check scanner result
grep "1.3.1.1" /tmp/vijenex-test/vijenex-cis-results.csv

# Check OpenSCAP result
grep -A 2 "libselinux" /tmp/openscap-report.html
```

**Verify:** Both scanners agree on result

#### Test 4: Service Status
```bash
# Check actual state
systemctl is-enabled firewalld
systemctl is-active firewalld

# Check scanner result
grep "firewalld" /tmp/vijenex-test/vijenex-cis-results.csv
```

**Verify:** Scanner correctly detects service status

#### Test 5: AIDE
```bash
# Check actual state
rpm -q aide
ls -l /etc/cron.d/aide

# Check scanner result
grep -i "aide" /tmp/vijenex-test/vijenex-cis-results.csv

# Check OpenSCAP result
grep -A 2 "AIDE" /tmp/openscap-report.html
```

**Verify:** Both scanners agree on result

---

## 📊 Expected Results After Fixes

### Before Fixes (Old Scan):
```
PASS:    67
FAIL:    122 (includes ~20 false positives)
MANUAL:  181
SKIPPED: 0
Total:   370
```

### After Fixes (Expected):
```
PASS:    67-80
FAIL:    100-110 (false positives removed)
MANUAL:  181
SKIPPED: 30-50 (mount options on non-existent partitions)
Total:   378-421
```

### Comparison with OpenSCAP:
```
OpenSCAP:  152 pass, 104 fail (256 total)
Vijenex:   ~75 pass, ~105 fail, ~40 skip (220 automated)
```

**Acceptable Difference:** Within 20 controls

---

## ✅ Pass Criteria

### CSV Output:
- [ ] All rows have exactly 7 columns
- [ ] No broken lines or malformed data
- [ ] Titles are complete (not truncated mid-word)
- [ ] Descriptions are complete
- [ ] Special characters properly escaped

### HTML Output:
- [ ] Opens without errors
- [ ] JavaScript works (click to expand)
- [ ] All controls display properly
- [ ] Descriptions show CIS text (not overwritten)
- [ ] Titles are complete
- [ ] Status badges show correct colors

### Accuracy:
- [ ] Mount options return SKIPPED when partition doesn't exist
- [ ] SELinux detection works correctly
- [ ] Service status checks work correctly
- [ ] False positive count < 10
- [ ] Results match OpenSCAP within 20 controls

### Performance:
- [ ] Scan completes in < 3 minutes
- [ ] No crashes or errors
- [ ] All 218 Level 1 controls execute

---

## 🚫 Fail Criteria (DO NOT DEPLOY IF):

- [ ] CSV has broken lines or malformed data
- [ ] HTML doesn't display properly
- [ ] Titles or descriptions are truncated
- [ ] More than 10 false positives
- [ ] Results differ from OpenSCAP by > 30 controls
- [ ] Scanner crashes or hangs
- [ ] Less than 200 Level 1 controls execute

---

## 📝 Test Results Template

```
Date: ___________
Tester: ___________
Server: ___________

CSV Output:
  ✓/✗ 7 columns
  ✓/✗ No broken lines
  ✓/✗ Complete titles
  ✓/✗ Complete descriptions

HTML Output:
  ✓/✗ Opens correctly
  ✓/✗ JavaScript works
  ✓/✗ Controls expand/collapse
  ✓/✗ Descriptions preserved

Results:
  PASS: _____
  FAIL: _____
  SKIP: _____
  MANUAL: _____
  Total Automated: _____

OpenSCAP Comparison:
  OpenSCAP pass: _____
  OpenSCAP fail: _____
  Difference: _____

False Positives Found:
  1. ___________
  2. ___________
  3. ___________

Manual Verification:
  ✓/✗ cramfs check correct
  ✓/✗ /tmp mount options correct
  ✓/✗ SELinux check correct
  ✓/✗ Service checks correct
  ✓/✗ AIDE checks correct

Overall: PASS / FAIL

Notes:
___________
___________
```

---

## 🎯 Next Steps After Testing

### If All Tests Pass:
1. Document test results
2. Create deployment package
3. Deploy to pilot servers (2-3)
4. Monitor for 1 week
5. Deploy to all 50 servers

### If Tests Fail:
1. Document failures
2. Fix issues in code
3. Rebuild scanner
4. Re-run all tests
5. Do NOT deploy until all tests pass

---

**CRITICAL:** Do not skip any tests. All must pass before production deployment.
