# OpenSCAP Installation and Scanning Guide

## Install OpenSCAP on RHEL 8

```bash
# Install OpenSCAP scanner and security guide
sudo dnf install -y openscap-scanner scap-security-guide

# Verify installation
oscap --version
```

## Available Security Profiles

```bash
# List all available profiles
oscap info /usr/share/xml/scap/ssg/content/ssg-rhel8-ds.xml

# Common profiles:
# - xccdf_org.ssgproject.content_profile_cis          (CIS RHEL 8 Benchmark)
# - xccdf_org.ssgproject.content_profile_cis_server_l1 (CIS Level 1 Server)
# - xccdf_org.ssgproject.content_profile_cis_workstation_l1 (CIS Level 1 Workstation)
# - xccdf_org.ssgproject.content_profile_pci-dss      (PCI-DSS)
# - xccdf_org.ssgproject.content_profile_stig         (DISA STIG)
```

## Run CIS Benchmark Scan

### Option 1: CIS Level 1 Server Profile
```bash
sudo oscap xccdf eval \
  --profile xccdf_org.ssgproject.content_profile_cis_server_l1 \
  --results /tmp/openscap-results.xml \
  --report /tmp/openscap-report.html \
  /usr/share/xml/scap/ssg/content/ssg-rhel8-ds.xml
```

### Option 2: Full CIS Profile
```bash
sudo oscap xccdf eval \
  --profile xccdf_org.ssgproject.content_profile_cis \
  --results /tmp/openscap-results.xml \
  --report /tmp/openscap-report.html \
  /usr/share/xml/scap/ssg/content/ssg-rhel8-ds.xml
```

### Option 3: Generate Remediation Script (DO NOT RUN - AUDIT ONLY)
```bash
# Generate remediation bash script (for reference only)
sudo oscap xccdf generate fix \
  --profile xccdf_org.ssgproject.content_profile_cis_server_l1 \
  --output /tmp/openscap-remediation.sh \
  /tmp/openscap-results.xml
```

## View Results

```bash
# View HTML report
firefox /tmp/openscap-report.html

# Or copy to Windows
# (Run on Linux first: sudo cp /tmp/openscap-report.html /home/vapt/)
# Then on Windows:
# pscp -i your-key.ppk vapt@172.24.0.136:/home/vapt/openscap-report.html C:\Users\vaptuser\Documents\
```

## Compare with Vijenex Scanner

### OpenSCAP Output Format:
- **pass**: Control passed
- **fail**: Control failed
- **notchecked**: Manual check required
- **notapplicable**: Not applicable to system
- **notselected**: Not in selected profile
- **error**: Check failed to run

### Vijenex Scanner Output Format:
- **PASS**: Control passed
- **FAIL**: Control failed
- **MANUAL**: Manual verification required
- **SKIPPED**: Level 2 control (when running Level 1)

## Key Differences

| Feature | OpenSCAP | Vijenex Scanner |
|---------|----------|-----------------|
| Controls | ~200 (varies by profile) | 275 (complete CIS) |
| Manual Checks | "notchecked" status | "MANUAL" with priority |
| Remediation | Auto-generates scripts | Audit only, no scripts |
| Report Format | XML + HTML | CSV + HTML |
| Speed | Slower (~5-10 min) | Faster (~1-2 min) |
| Customization | Limited | Fully customizable |
| Priority Levels | No | Yes (Critical/High/Medium/Low) |

## Example OpenSCAP Scan

```bash
# Full scan with all outputs
sudo oscap xccdf eval \
  --profile xccdf_org.ssgproject.content_profile_cis_server_l1 \
  --results /tmp/openscap-results.xml \
  --report /tmp/openscap-report.html \
  --oval-results \
  /usr/share/xml/scap/ssg/content/ssg-rhel8-ds.xml

# Check exit code
echo "Exit code: $?"
# 0 = all passed
# 1 = error
# 2 = some checks failed
```

## Copy Reports to Windows

```bash
# On Linux
sudo cp /tmp/openscap-report.html /home/vapt/
sudo cp /tmp/openscap-results.xml /home/vapt/
sudo chown vapt:vapt /home/vapt/openscap-*
```

```cmd
REM On Windows
pscp -i "C:\Users\vaptuser\Documents\Linux_Server_Putty_access_2ndSets\ppk\Prod_motorcovernoteapp_2022 server_172.24.0.136.ppk" vapt@172.24.0.136:/home/vapt/openscap-report.html C:\Users\vaptuser\Documents\

pscp -i "C:\Users\vaptuser\Documents\Linux_Server_Putty_access_2ndSets\ppk\Prod_motorcovernoteapp_2022 server_172.24.0.136.ppk" vapt@172.24.0.136:/home/vapt/openscap-results.xml C:\Users\vaptuser\Documents\
```

## Analyze OpenSCAP Results

```bash
# Count results by status
grep -o 'result="[^"]*"' /tmp/openscap-results.xml | sort | uniq -c

# Example output:
#  45 result="pass"
#  23 result="fail"
#  120 result="notchecked"
#  15 result="notapplicable"
```

## Side-by-Side Comparison Command

```bash
# Run both scanners
echo "=== Running Vijenex Scanner ==="
sudo /root/linux-cis-scanner/rhel-8/vijenex-cis-amd64 --profile Level1 --output-dir /tmp/vijenex

echo "=== Running OpenSCAP ==="
sudo oscap xccdf eval \
  --profile xccdf_org.ssgproject.content_profile_cis_server_l1 \
  --results /tmp/openscap-results.xml \
  --report /tmp/openscap-report.html \
  /usr/share/xml/scap/ssg/content/ssg-rhel8-ds.xml

echo "=== Comparison ==="
echo "Vijenex: $(grep -c "^" /tmp/vijenex/reports/vijenex-cis-results.csv) controls"
echo "OpenSCAP: $(grep -c 'rule-result' /tmp/openscap-results.xml) controls"
```
