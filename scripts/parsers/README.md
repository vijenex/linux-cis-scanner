# CIS Benchmark Parsers

Utility scripts to parse CIS benchmark documents and generate milestone JSON files.

## parse-cis-rtf.py

Parses CIS benchmark RTF files and generates milestone JSON files for the Go scanner.

### Usage

```bash
python3 parse-cis-rtf.py <rtf_file> <output_dir> <os_name> <version>
```

### Examples

**RHEL 9:**
```bash
python3 parse-cis-rtf.py \
  ~/Desktop/CIS-Official-docs/CIS_Red_Hat_Enterprise_Linux_9_Benchmark_v2.0.0.rtf \
  ../../rhel-9/go-scanner/milestones \
  "RHEL 9" \
  "v2.0.0"
```

**Ubuntu 22.04:**
```bash
python3 parse-cis-rtf.py \
  ~/Desktop/CIS-Official-docs/CIS_Ubuntu_22.04_Benchmark_v1.0.0.rtf \
  ../../ubuntu-22.04/go-scanner/milestones \
  "Ubuntu 22.04" \
  "v1.0.0"
```

**Ubuntu 24.04:**
```bash
python3 parse-cis-rtf.py \
  ~/Desktop/CIS-Official-docs/CIS_Ubuntu_24.04_Benchmark_v1.0.0.rtf \
  ../../ubuntu-24.04/go-scanner/milestones \
  "Ubuntu 24.04" \
  "v1.0.0"
```

## Output

The script generates:
- Multiple milestone JSON files (one per section)
- Each milestone contains controls with:
  - Control ID
  - Title
  - Profile (Level1/Level2)
  - Type (KernelModule, MountPoint, MountOption, etc.)
  - Automated/Manual flag
  - Severity
  - CIS reference

## Notes

- Place all CIS benchmark RTF files in `~/Desktop/CIS-Official-docs/`
- The parser automatically detects control types based on title patterns
- Level 2 controls are automatically tagged
- Generated files are ready to use with the Go scanner
