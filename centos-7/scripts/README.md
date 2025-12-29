# CentOS 7 Milestone Generator

This script parses the official CIS CentOS Linux 7 Benchmark PDF and generates milestone JSON files.

## Prerequisites

1. **Install PyPDF2**:
   ```bash
   pip install PyPDF2
   ```

2. **Download the official CIS PDF**:
   - File: `CIS_CentOS_Linux_7_Benchmark_v3.1.2.pdf`
   - Should be in your downloads folder or project downloads directory

## Usage

```bash
cd centos-7/scripts
python3 parse-centos7-cis.py <path_to_pdf> <output_directory>
```

### Example

If the PDF is in your Downloads folder:
```bash
python3 parse-centos7-cis.py ~/Downloads/CIS_CentOS_Linux_7_Benchmark_v3.1.2.pdf ../go-scanner/milestones
```

If the PDF is in a project downloads folder:
```bash
python3 parse-centos7-cis.py ../../downloads/CIS_CentOS_Linux_7_Benchmark_v3.1.2.pdf ../go-scanner/milestones
```

## What It Does

1. ✅ Extracts all controls from the PDF
2. ✅ **Filters to only Level 1 controls** (excludes Level 2)
3. ✅ Detects control types automatically
4. ✅ Extracts description, remediation, and audit commands
5. ✅ Generates milestone JSON files organized by section
6. ✅ Excludes unsupported controls

## Output

The script generates milestone files in the format:
- `milestone-1-1.json` (Section 1.1)
- `milestone-1-2.json` (Section 1.2)
- etc.

Each milestone file contains only Level 1 controls for that section.

## Notes

- The script automatically excludes Level 2 controls
- Only automated and manual Level 1 controls are included
- Control types are auto-detected (KernelModule, MountPoint, SysctlParameter, etc.)
- Descriptions and remediation steps are extracted from the official PDF

