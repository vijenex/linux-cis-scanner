# Generate Milestone Files for CentOS 7

## Quick Start

1. **Locate the PDF**: The official CIS CentOS Linux 7 Benchmark PDF should be in your downloads folder:
   - File name: `CIS_CentOS_Linux_7_Benchmark_v3.1.2.pdf`
   - Common locations:
     - `~/Downloads/CIS_CentOS_Linux_7_Benchmark_v3.1.2.pdf`
     - `./downloads/CIS_CentOS_Linux_7_Benchmark_v3.1.2.pdf`
     - Project downloads folder

2. **Install dependencies**:
   ```bash
   pip install PyPDF2
   ```

3. **Run the parser**:
   ```bash
   cd centos-7/scripts
   python3 parse-centos7-cis.py <path_to_pdf> ../go-scanner/milestones
   ```

## Example Commands

### If PDF is in Downloads folder:
```bash
cd centos-7/scripts
python3 parse-centos7-cis.py ~/Downloads/CIS_CentOS_Linux_7_Benchmark_v3.1.2.pdf ../go-scanner/milestones
```

### If PDF is in project downloads folder:
```bash
cd centos-7/scripts
python3 parse-centos7-cis.py ../../downloads/CIS_CentOS_Linux_7_Benchmark_v3.1.2.pdf ../go-scanner/milestones
```

## What Gets Generated

The script will create milestone JSON files in `centos-7/go-scanner/milestones/`:
- Only **Level 1 controls** (Level 2 excluded)
- Only **supported controls** for CentOS 7
- Proper control types detected automatically
- Official descriptions and remediation from PDF

## Verification

After running, check the output:
```bash
ls -la centos-7/go-scanner/milestones/
```

You should see files like:
- `milestone-1-1.json`
- `milestone-1-2.json`
- `milestone-2-1.json`
- etc.

## Troubleshooting

**If PDF not found:**
- Check the file name matches exactly: `CIS_CentOS_Linux_7_Benchmark_v3.1.2.pdf`
- Verify the path is correct
- Check if file has different name or location

**If PyPDF2 error:**
```bash
pip install PyPDF2
```

**If no controls extracted:**
- Verify PDF is the correct version (v3.1.2)
- Check PDF is not corrupted
- Review parser output for errors

