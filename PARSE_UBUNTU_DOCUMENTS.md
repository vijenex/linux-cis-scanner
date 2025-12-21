# Parse Ubuntu CIS Documents - Quick Guide

## Overview

This guide helps you extract complete descriptions and remediation steps from official CIS Ubuntu benchmark documents for both Ubuntu 22.04 and 24.04.

## Prerequisites

1. **Official CIS Documents** (PDF or RTF format):
   - CIS Ubuntu 22.04 LTS Benchmark
   - CIS Ubuntu 24.04 LTS Benchmark

2. **Python Dependencies**:
   ```bash
   pip install PyPDF2  # For PDF files
   ```

## Quick Start

### Step 1: Install Dependencies

```bash
pip install PyPDF2
```

### Step 2: Run Parser for Ubuntu 22.04

```bash
cd /Users/sowmya/Desktop/Vijenex/linux-cis-scanner

python3 scripts/parsers/parse-ubuntu-cis-complete.py \
  <path-to-ubuntu-22.04-pdf> \
  ubuntu-22.04/go-scanner/milestones \
  22.04
```

**Example:**
```bash
python3 scripts/parsers/parse-ubuntu-cis-complete.py \
  ~/Downloads/CIS_Ubuntu_22.04_LTS_Benchmark_v1.0.0.pdf \
  ubuntu-22.04/go-scanner/milestones \
  22.04
```

### Step 3: Run Parser for Ubuntu 24.04

```bash
python3 scripts/parsers/parse-ubuntu-cis-complete.py \
  <path-to-ubuntu-24.04-pdf> \
  ubuntu-24.04/go-scanner/milestones \
  24.04
```

**Example:**
```bash
python3 scripts/parsers/parse-ubuntu-cis-complete.py \
  ~/Downloads/CIS_Ubuntu_24.04_LTS_Benchmark_v1.0.0.pdf \
  ubuntu-24.04/go-scanner/milestones \
  24.04
```

## What the Parser Does

1. **Extracts Complete Descriptions**:
   - Full text from "Description:" section
   - No breaks or truncation
   - Preserves paragraph structure
   - Removes PDF/RTF artifacts

2. **Extracts Complete Remediation**:
   - Full remediation steps from "Remediation:" section
   - Preserves command formatting
   - Maintains line breaks for commands
   - No breaks or truncation

3. **Updates All Milestone Files**:
   - Automatically updates all milestone JSON files
   - Removes `reference_note` when actual content is found
   - Preserves all other fields (ID, title, type, etc.)

## Verification

After parsing, verify the results:

```bash
# Check a sample control
cat ubuntu-22.04/go-scanner/milestones/milestone-1-1.json | \
  jq '.controls[0] | {id, title, description: (.description | length), remediation: (.remediation | length)}'
```

You should see:
- `description`: A number (character count) - should be > 0
- `remediation`: A number (character count) - should be > 0

## Expected Output

The parser will show:
```
✅ Extracted X,XXX characters from document
📋 Found XX milestone files
🔄 Parsing and updating milestone files...
  [1/XX] ✓ milestone-1-1.json: XX descriptions, XX remediations
  ...
✅ PARSING COMPLETE
📊 Total descriptions added: XXX
📊 Total remediations added: XXX
```

## Notes

- The parser handles multi-line descriptions and remediation properly
- Commands in remediation are preserved with proper formatting
- Paragraph breaks are maintained for readability
- PDF artifacts are automatically removed

## Troubleshooting

### Document Not Found

If you get "CIS document not found":
- Check the file path is correct
- Ensure the file exists and is readable
- Use absolute path if relative path doesn't work

### Controls Not Found

If some controls are not found:
- Control IDs in milestone files may differ from document
- Check document version matches milestone files
- Some controls may be missing from the document

### Incomplete Extraction

If descriptions/remediations seem incomplete:
- Check document format (PDF vs RTF)
- Verify section markers in document (Description:, Remediation:)
- Try RTF format if PDF parsing has issues

## After Parsing

Once parsing is complete:
1. ✅ All controls will have complete `description` field
2. ✅ All controls will have complete `remediation` field
3. ✅ `reference_note` fields will be removed
4. ✅ Ready to use with the Go scanner

Test the scanner:
```bash
cd ubuntu-22.04/go-scanner
go build -o /tmp/test-scanner ./cmd
sudo /tmp/test-scanner --output-dir /tmp/test-reports
```

