# Linux CIS Scanner v2.0.0 - Phase 1 Changes
**Release Date:** 2025-01-15  
**Status:** Phase 1 Complete (Scanner Signature + CSV Format)

---

## Overview
This release brings the Linux CIS scanner in line with the Windows CIS scanner quality standards. Phase 1 focuses on simplifying the scanner signature and updating the CSV format to match Windows scanner conventions.

---

## Changes Implemented

### 1. Scanner Signature Simplified ✅

**BEFORE (v1.0.9):**
```
██╗   ██╗██╗     ██╗███████╗███╗   ██╗███████╗██╗  ██╗
██║   ██║██║     ██║██╔════╝████╗  ██║██╔════╝╚██╗██╔╝
██║   ██║██║     ██║█████╗  ██╔██╗ ██║█████╗   ╚███╔╝ 
╚██╗ ██╔╝██║██   ██║██╔══╝  ██║╚██╗██║██╔══╝   ██╔██╗ 
 ╚████╔╝ ██║╚█████╔╝███████╗██║ ╚████║███████╗██╔╝ ██╗
  ╚═══╝  ╚═╝ ╚════╝ ╚══════╝╚═╝  ╚═══╝╚══════╝╚═╝  ╚═╝

                 Vijenex CIS Scanner
           Enterprise Linux Security Compliance
═════════════════════════════════════════════════════════
```

**AFTER (v2.0.0):**
```
=============================================================
                        VIJENEX                              
      Ubuntu 22.04.3 LTS CIS Scanner           
           Powered by Vijenex Security Platform             
        https://github.com/vijenex/linux-cis-scanner        
=============================================================
```

**Benefits:**
- ✅ Cleaner, more professional appearance
- ✅ Shows actual distribution name dynamically
- ✅ Matches Windows scanner style
- ✅ Includes GitHub link for reference
- ✅ Removes unnecessary ASCII art
- ✅ Easier to read in terminal

---

### 2. CSV Format Updated ✅

**BEFORE (v1.0.9) - 6 Columns:**
```csv
ID,Control,Section,Status,CIS_Reference,Reference_Note
1.1.1,Ensure mounting of cramfs filesystems is disabled,Initial Setup,PASS,https://...,Refer to official CIS benchmark
```

**AFTER (v2.0.0) - 7 Columns:**
```csv
Id,Title,Section,Status,CISReference,Remediation,Description
1.1.1,Ensure mounting of cramfs filesystems is disabled,Initial Setup,PASS,https://...,Edit /etc/modprobe.d/cramfs.conf,Kernel module availability verified
```

**Changes:**
- ✅ Column names match Windows scanner exactly
- ✅ Added **Remediation** column with fix instructions
- ✅ Added **Description** column explaining what was checked
- ✅ Removed generic **Reference_Note** column
- ✅ More useful for end users and compliance teams

---

### 3. Result Object Structure Updated ✅

**BEFORE (v1.0.9):**
```python
result = {
    "id": "1.1.1",
    "title": "Control name",
    "section": "Section 1",
    "status": "PASS",
    "current": "Module blacklisted",
    "expected": "Module not_available",
    "evidence": "Module cramfs: blacklisted=True, loaded=False"
}
```

**AFTER (v2.0.0):**
```python
result = {
    "id": "1.1.1",
    "title": "Control name",
    "section": "Section 1",
    "status": "PASS",
    "actual_value": "Module blacklisted and not loaded",
    "evidence_command": "lsmod | grep cramfs",
    "description": "Kernel module availability verified",
    "remediation": "Edit /etc/modprobe.d/cramfs.conf"
}
```

**Benefits:**
- ✅ `actual_value` shows what system currently has
- ✅ `evidence_command` shows how to verify manually
- ✅ `description` explains what was checked
- ✅ `remediation` shows how to fix failures
- ✅ Removed confusing `current`/`expected`/`evidence` fields

---

### 4. Summary Display Improved ✅

**BEFORE (v1.0.9):**
```
🎯 Scan Completed Successfully!
✓ Passed: 250
✗ Failed: 30
⚠ Manual: 10
📊 Total Controls: 290
```

**AFTER (v2.0.0):**
```
=============================================================
                    SCAN COMPLETED                           
=============================================================
Total Checks: 290
Passed: 250
Failed: 30
Manual: 10
Success Rate: 86.2%
=============================================================
```

**Benefits:**
- ✅ Matches Windows scanner box design
- ✅ Adds success rate calculation
- ✅ More professional appearance
- ✅ Removes emoji for enterprise use
- ✅ Cleaner formatting

---

### 5. Check Methods Updated ✅

Updated all check methods to return new field names:
- `check_file_permissions()` - Returns `actual_value`, `evidence_command`, `description`
- `check_service_status()` - Returns `actual_value`, `evidence_command`, `description`
- `check_kernel_parameter()` - Returns `actual_value`, `evidence_command`, `description`
- `check_package_installed()` - Returns `actual_value`, `evidence_command`, `description`

**Example:**
```python
# BEFORE
return {
    "status": "PASS",
    "current": "Mode: 644, Owner: root, Group: root",
    "expected": "Mode: 644, Owner: root, Group: root",
    "evidence": "Permissions correct"
}

# AFTER
return {
    "status": "PASS",
    "actual_value": "Mode: 644, Owner: root, Group: root",
    "evidence_command": "ls -l /etc/passwd",
    "description": "File permissions verified"
}
```

---

## Files Modified

1. **ubuntu-22.04/scripts/vijenex-cis.py** ✅
   - Scanner signature simplified (lines 1-10)
   - Result object structure updated (execute_control method)
   - CSV generation updated (generate_csv_report method)
   - Summary display improved (scan_milestones method)
   - Check methods updated (4 methods modified)

2. **ubuntu-24.04/scripts/vijenex-cis.py** ✅
   - Copied from ubuntu-22.04 (same changes applied)

**Note:** Other OS folders (rhel-8, rhel-9, centos-7, debian-11, ubuntu-20.04) do not have full scanners yet, so Phase 1 changes only apply to Ubuntu 22.04 and 24.04.

---

## Testing Checklist

- [ ] Run scanner on Ubuntu 22.04 system
- [ ] Verify new signature displays correctly
- [ ] Verify CSV has 7 columns with correct names
- [ ] Verify CSV contains remediation and description
- [ ] Verify summary shows success rate
- [ ] Verify HTML report still works
- [ ] Test with --format csv option
- [ ] Test with --format html option
- [ ] Test with --format both option

---

## Backward Compatibility

⚠️ **BREAKING CHANGES:**
- CSV format changed from 6 columns to 7 columns
- Column names changed (ID → Id, Control → Title, etc.)
- Scripts parsing old CSV format will need updates

**Migration Guide:**
```python
# OLD CSV parsing
df = pd.read_csv('results.csv')
control_id = df['ID']
control_name = df['Control']
reference = df['Reference_Note']

# NEW CSV parsing
df = pd.read_csv('results.csv')
control_id = df['Id']
control_name = df['Title']
remediation = df['Remediation']
description = df['Description']
```

---

## Next Steps (Phase 2)

### Planned for v2.1.0:
1. **Enhance HTML Report**
   - Add "Actual Value" column
   - Add "Evidence Command" column
   - Add "Remediation" column
   - Remove generic "Details" column

2. **Add PDF Report**
   - Create PDF-ready HTML with print button
   - Add @media print CSS rules
   - Add important notes section
   - Add remediation best practices

3. **Add Word Report**
   - Create Word-compatible HTML
   - Use Calibri font
   - Professional color scheme
   - Usage instructions

4. **Add Output Format Control**
   - `--format html` - HTML only
   - `--format csv` - CSV only
   - `--format pdf` - PDF-ready HTML
   - `--format word` - Word-compatible HTML
   - `--format all` - All formats

---

## Known Issues

None identified in Phase 1 changes.

---

## Contributors

- Satish Korra - Phase 1 implementation
- Based on Windows CIS Scanner design patterns

---

## References

- Windows CIS Scanner v1.8.3
- CIS Ubuntu Linux 22.04 LTS Benchmark v1.0.0
- Report Generation Comparison Document

---

**End of Phase 1 Changes**
