# Updating Ubuntu 24.04 Milestone Files

This guide explains how to update milestone files with description and remediation steps from the official CIS Ubuntu 24.04 Benchmark document.

## Prerequisites

1. **Official CIS Document**: Download the official CIS Ubuntu 24.04 LTS Benchmark (PDF or RTF format)
2. **Python Dependencies**: 
   ```bash
   pip install PyPDF2  # For PDF files
   # OR
   pip install striprtf  # For RTF files
   ```

## Usage

### Step 1: Locate Your CIS Document

Place your official CIS Ubuntu 24.04 Benchmark document in a known location, for example:
- `~/Downloads/CIS_Ubuntu_24.04_LTS_Benchmark_v1.0.0.pdf`
- `~/Desktop/CIS-Official-docs/CIS_Ubuntu_24.04_Benchmark.rtf`

### Step 2: Run the Update Script

```bash
cd /path/to/linux-cis-scanner
python3 scripts/parsers/update-ubuntu-milestones.py \
  ~/Downloads/CIS_Ubuntu_24.04_LTS_Benchmark_v1.0.0.pdf \
  ubuntu-24.04/go-scanner/milestones \
  24.04
```

### Step 3: Verify Updates

Check a milestone file to ensure description and remediation fields are populated:

```bash
cat ubuntu-24.04/go-scanner/milestones/milestone-1-1.json | jq '.controls[0] | {id, title, description, remediation}'
```

## What Gets Updated

The script will:
- ✅ Extract **description** from the "Description:" section of each control
- ✅ Extract **remediation** from the "Remediation:" section of each control
- ✅ Update all milestone JSON files
- ✅ Remove `reference_note` fields when actual content is found
- ✅ Keep `cis_reference` field for official document reference

## Fields in Updated Controls

After running the script, each control will have:

```json
{
  "id": "1.1.1.1",
  "title": "Ensure cramfs kernel module is not available",
  "section": "1.1.1 Configure Filesystem Kernel Modules",
  "profile": "Level1",
  "automated": true,
  "type": "KernelModule",
  "module_name": "cramfs",
  "expected_status": "not_available",
  "cis_reference": "CIS Ubuntu 24.04 - 1.1.1.1 | Level 1",
  "description": "The cramfs filesystem type is a compressed read-only Linux filesystem...",
  "remediation": "Run the following commands to unload and disable the cramfs kernel module:\n# modprobe -r cramfs..."
}
```

## Troubleshooting

### Script can't find controls

If the script reports "Updated 0 fields", the control ID format in the document might differ. Check:
- Control IDs in document: `1.1.1.1` vs `1.1.1.1 (L1)`
- Document format (PDF vs RTF)
- Text extraction quality

### Missing descriptions/remediations

Some controls might not have extractable content. The script will:
- Leave existing fields unchanged if extraction fails
- Log which files were updated

### PDF parsing issues

If PDF parsing fails:
- Try converting PDF to RTF first
- Use a different PDF library (pypdf, pdfplumber)
- Extract text manually and save as RTF

## Manual Updates

If automatic extraction doesn't work, you can manually update milestone files:

1. Open the milestone JSON file
2. For each control, add:
   - `"description": "..."` - from the Description section
   - `"remediation": "..."` - from the Remediation section
3. Remove `"reference_note"` field if present
4. Save the file

## Verification

After updating, verify the scanner works:

```bash
cd ubuntu-24.04/go-scanner
go build -o /tmp/test-scanner ./cmd
/tmp/test-scanner --output-dir /tmp/test-reports
```

Check the HTML report to ensure descriptions and remediation steps are displayed correctly.

