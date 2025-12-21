# Parse Ubuntu CIS Documents - Complete Instructions

This guide explains how to extract complete descriptions and remediation steps from official CIS Ubuntu benchmark documents.

## Prerequisites

1. **Official CIS Documents**: 
   - CIS Ubuntu 22.04 LTS Benchmark (PDF or RTF)
   - CIS Ubuntu 24.04 LTS Benchmark (PDF or RTF)

2. **Python Dependencies**:
   ```bash
   pip install PyPDF2  # For PDF files
   # OR
   pip install striprtf  # For RTF files
   ```

## Quick Start

### Step 1: Locate Your CIS Documents

Place your official CIS Ubuntu benchmark documents in a known location, for example:
- `~/Downloads/CIS_Ubuntu_22.04_LTS_Benchmark_v1.0.0.pdf`
- `~/Downloads/CIS_Ubuntu_24.04_LTS_Benchmark_v1.0.0.pdf`

### Step 2: Run the Parser

**For Ubuntu 22.04:**
```bash
cd /Users/sowmya/Desktop/Vijenex/linux-cis-scanner
python3 scripts/parsers/parse-ubuntu-cis-complete.py \
  ~/Downloads/CIS_Ubuntu_22.04_LTS_Benchmark.pdf \
  ubuntu-22.04/go-scanner/milestones \
  22.04
```

**For Ubuntu 24.04:**
```bash
python3 scripts/parsers/parse-ubuntu-cis-complete.py \
  ~/Downloads/CIS_Ubuntu_24.04_LTS_Benchmark.pdf \
  ubuntu-24.04/go-scanner/milestones \
  24.04
```

### Step 3: Verify Results

Check a milestone file to ensure descriptions and remediation are complete:

```bash
# Check first control
cat ubuntu-22.04/go-scanner/milestones/milestone-1-1.json | jq '.controls[0] | {id, title, description, remediation}'
```

## What Gets Extracted

The parser extracts:

1. **Complete Description**: 
   - Full text from "Description:" section
   - Preserves paragraph structure
   - No breaks or truncation
   - Cleaned of PDF/RTF artifacts

2. **Complete Remediation**:
   - Full remediation steps from "Remediation:" section
   - Preserves command formatting
   - Maintains line breaks for commands
   - No breaks or truncation

## Features

- ✅ **Complete Text**: No truncation, extracts full descriptions and remediation
- ✅ **Proper Formatting**: Preserves paragraph structure and command formatting
- ✅ **Multi-line Support**: Handles descriptions and remediation spanning multiple lines
- ✅ **Clean Output**: Removes PDF/RTF artifacts while preserving content
- ✅ **Error Handling**: Reports controls not found in document

## Troubleshooting

### Controls Not Found

If some controls are not found:
- Check if control IDs in milestone files match the document
- Some controls may have different numbering in the document
- Verify the document version matches the milestone files

### PDF Parsing Issues

If PDF parsing fails:
- Try converting PDF to RTF first
- Use a different PDF library (pypdf, pdfplumber)
- Check if the PDF is text-based (not scanned image)

### Incomplete Extraction

If descriptions/remediations are incomplete:
- The document may have different section markers
- Check the document format (PDF vs RTF)
- Verify the section names match (Description:, Remediation:)

## Output

After running the parser, each control will have:

```json
{
  "id": "1.1.1.1",
  "title": "Ensure cramfs kernel module is not available",
  "description": "The cramfs filesystem type is a compressed read-only Linux filesystem embedded in small footprint systems. Removing support for unneeded filesystem types reduces the local attack surface of the system.",
  "remediation": "Run the following commands to unload and disable the cramfs kernel module:\n# modprobe -r cramfs 2>/dev/null\n# rmmod cramfs 2>/dev/null\n# printf '%s\\n' '' 'install cramfs /bin/false' >> /etc/modprobe.d/60-cramfs.conf\n# printf '%s\\n' '' 'blacklist cramfs' >> /etc/modprobe.d/60-cramfs.conf"
}
```

## Verification

After parsing, verify the scanner works:

```bash
cd ubuntu-22.04/go-scanner
go build -o /tmp/test-scanner ./cmd
/tmp/test-scanner --output-dir /tmp/test-reports
```

Check the HTML report to ensure descriptions and remediation steps are displayed correctly.

