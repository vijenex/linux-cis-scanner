# Universal Audit Report Generator

Automated CIS compliance audit report generator for multiple operating systems.

## Folder Structure

```
Universal-Audit-Report-Generator/
├── cis-benchmarks/          # Official CIS benchmark documents
│   ├── rhel-8/
│   │   └── CIS_Red_Hat_Enterprise_Linux_8_Benchmark_v4.0.0.txt.rtf
│   ├── windows-2022/
│   └── ubuntu-22/
├── scan-results/            # Extracted scan results in CSV format
│   ├── rhel-8/
│   │   ├── 172.24.0.136_controls.csv
│   │   └── 172.16.0.141_controls.csv
│   └── windows-2022/
├── scripts/                 # Parser and generator scripts
│   ├── rhel8_parser.py
│   ├── rhel8_generator.py
│   └── universal-audit-report-generator.py
├── generated-reports/       # Final audit reports
│   ├── Red-Hat-Enterprise-Linux-8-CIS-Audit-Report.docx
│   └── Windows-Server-2022-CIS-Audit-Report.docx
└── README.md
```

## How to Generate RHEL-8 Audit Report

### Step 1: Place OpenSCAP Scan Results
Put OpenSCAP RTF scan results in a temporary location (e.g., Downloads/RHEL-8/UAT/)

### Step 2: Extract Controls to CSV
```bash
cd /Users/satish.korra/Documents/Universal-Audit-Report-Generator
python3 << 'EOF'
from striprtf.striprtf import rtf_to_text
import csv, re

files = {
    '172.24.0.136': '/path/to/172.24.0.136.txt.rtf',
    '172.16.0.141': '/path/to/172.16.0.141.txt.rtf'
}

for ip, filepath in files.items():
    with open(filepath, 'r') as f:
        text = rtf_to_text(f.read())
    
    controls = []
    for line in text.split('\n'):
        if re.search(r'\|(medium|high|low|other)\|(pass|fail)\|', line):
            parts = line.split('|')
            if len(parts) >= 3:
                title = parts[0].strip()
                severity = parts[1].strip()
                result = parts[2].strip()
                if title and result in ['pass', 'fail']:
                    controls.append([title, severity, result.capitalize()])
    
    with open(f'scan-results/rhel-8/{ip}_controls.csv', 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Title', 'Severity', 'Result'])
        writer.writerows(controls)
    
    print(f"{ip}: {len(controls)} controls extracted")
EOF
```

### Step 3: Generate Audit Report
```bash
cd scripts
python3 rhel8_generator.py
```

Output: `generated-reports/Red-Hat-Enterprise-Linux-8-CIS-Audit-Report.docx`

## How to Generate Windows Audit Report

```bash
cd /Users/satish.korra/Documents/Universal-Audit-Report-Generator
python3 universal-audit-report-generator.py <scan_folder> <cis_rtf> <version>
```

Example:
```bash
python3 universal-audit-report-generator.py \
  /path/to/windows-scans \
  cis-benchmarks/windows-2022/CIS_Windows_Server_2022.rtf \
  2022
```

## Adding New OS Support

1. Create folder: `cis-benchmarks/<os-name>/`
2. Add CIS benchmark RTF file
3. Create folder: `scan-results/<os-name>/`
4. Create parser script: `scripts/<os-name>_parser.py`
5. Create generator script: `scripts/<os-name>_generator.py`

## Recovery Message for AI Assistant

**If context is lost, use this message:**

```
Please check the Universal-Audit-Report-Generator folder in Documents.
Generate RHEL-8 audit report by running:
cd /Users/satish.korra/Documents/Universal-Audit-Report-Generator/scripts
python3 rhel8_generator.py

The folder contains:
- CIS benchmarks in cis-benchmarks/rhel-8/
- Scan results CSV in scan-results/rhel-8/
- Generator scripts in scripts/
- Output in generated-reports/
```

## Requirements

```bash
pip3 install python-docx striprtf --break-system-packages
```

## Notes

- OpenSCAP may report different control counts per system based on installed packages/services
- Controls marked "N/A" were not applicable to that specific system
- Always test remediation on Non-Production systems first
- Refer to official CIS benchmarks for detailed remediation steps

## Support

For issues or questions, check:
1. CSV files are properly formatted in scan-results/
2. CIS benchmark RTF exists in cis-benchmarks/
3. All Python dependencies are installed
4. Scripts are run from the correct directory
