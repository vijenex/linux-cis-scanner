# VIJENEX CIS SCANNER - PROJECT INSTRUCTIONS

## PROJECT OVERVIEW
**Goal**: Build a CIS compliance scanner for RHEL 8 that is BETTER than OpenSCAP
**Project Name**: Vijenex CIS Scanner
**Target**: CIS Red Hat Enterprise Linux 8 Benchmark v4.0.0
**Deadline**: 2 days to scan 50 RHEL 8 machines and provide consolidated audit report

## CRITICAL REQUIREMENTS
1. **AUTOMATION FIRST**: Scanner MUST match or exceed OpenSCAP's automation level (256+ automated controls)
2. **NO LAZY MANUAL MARKING**: Only mark controls as "Manual" if CIS documentation EXPLICITLY states "Manual"
3. **BETTER THAN OPENSCAP**: Our HTML reports must be more professional, detailed, and user-friendly
4. **ACCURATE IMPLEMENTATION**: Each control must follow CIS v4.0.0 documentation exactly

## PROJECT STRUCTURE
```
/Users/satish.korra/Desktop/Linux-CIS-Audit-code/
├── rhel-8/
│   ├── scan.sh                      # ⭐ WRAPPER SCRIPT - Use this to run scanner!
│   ├── scripts/
│   │   ├── vijenex-cis.py          # Main scanner script (Python)
│   │   ├── auto-add-controls.py    # Automated control extractor
│   │   └── reorganize-milestones.py # Milestone organizer
│   ├── milestones/
│   │   ├── milestone-1-1.json      # Section 1.1 controls
│   │   ├── milestone-1-2.json      # Section 1.2 controls
│   │   └── ... (48 milestone files)
│   ├── reports/                     # Generated reports (HTML, CSV)
│   └── bin/                         # Go binary (if available)
├── README.md                        # Project overview
├── INSTRUCTIONS.md                  # This file - Full documentation
├── QUICK_START.md                   # Quick testing guide
└── CHANGELOG.md                     # Version history
```

## REFERENCE FILES
```
/Users/satish.korra/Desktop/CIS-controls-list/
├── openscap-rhel-8.rtf            # OpenSCAP results: 152 passed, 104 failed, 256 automated
└── vijenex-scan-rhel.rtf          # Initial Vijenex: 46 passed, 27 failed, 191 MANUAL (BAD!)
```

## SCANNER ARCHITECTURE

### Main Script: vijenex-cis.py
**Location**: `/Users/satish.korra/Desktop/Linux-CIS-Audit-code/rhel-8/scripts/vijenex-cis.py`

**Current Control Types Implemented**:
1. **KernelModule** - Check if kernel modules are disabled/loaded
2. **MountPoint** - Check if separate partition exists
3. **MountOption** - Check mount options (nodev, nosuid, noexec)
4. **ServiceStatus** - Check systemd service status
5. **PackageInstalled** - Check if package is installed

**Control Types NEEDED** (to match OpenSCAP):
- SysctlParameter - Check kernel parameters
- FilePermissions - Check file/directory permissions and ownership
- SSHConfig - Check SSH daemon configuration
- PAMConfig - Check PAM configuration
- FileContent - Check file content/grep patterns
- AuditRules - Check auditd rules
- GrubConfig - Check GRUB bootloader settings
- UserConfig - Check user/group configurations
- FirewallRules - Check firewall configurations

### Control Definition File: milestone-1-1.json
**Location**: `/Users/satish.korra/Desktop/Linux-CIS-Audit-code/rhel-8/milestones/milestone-1-1.json`

**Current Progress**: 22 controls implemented
- 11 kernel module controls (1.1.1.x)
- 4 /tmp partition controls (1.1.2.1.x)
- 4 /dev/shm controls (1.1.2.2.x)
- 3 /home partition controls (1.1.2.3.x)

**JSON Structure for Each Control**:
```json
{
  "control_id": "1.1.1.1",
  "title": "Control title from CIS doc",
  "description": "Full description from CIS doc",
  "rationale": "Full rationale from CIS doc",
  "remediation": "Exact remediation commands from CIS doc",
  "impact": "Impact statement from CIS doc (CRITICAL for Level 2)",
  "references": ["NIST references from CIS doc"],
  "severity": "Critical|High|Medium|Low",
  "level": 1 or 2,
  "automated": true or false,
  "type": "KernelModule|MountPoint|MountOption|etc",
  "audit": "Audit command from CIS doc",
  "parameters": {
    // Type-specific parameters
  }
}
```

## WORKFLOW - HOW WE ADD CONTROLS

### AUTOMATED METHOD (RECOMMENDED) ⚡

Use the **auto-add-controls.py** script to automatically extract controls from CIS document:

```bash
cd /Users/satish.korra/Desktop/Linux-CIS-Audit-code/rhel-8/scripts
python3 auto-add-controls.py --start <CONTROL_ID> --count <NUMBER>
```

**Examples:**
```bash
# Add 10 controls starting from 1.3.1.1
python3 auto-add-controls.py --start 1.3.1.1 --count 10

# Add 20 controls starting from 2.1.1
python3 auto-add-controls.py --start 2.1.1 --count 20

# Add 15 controls starting from 3.3.1.1
python3 auto-add-controls.py --start 3.3.1.1 --count 15
```

**What the script does:**
1. ✅ Reads CIS RHEL 8 Benchmark v4.0.0 document directly
2. ✅ Extracts control ID, title, description, rationale, impact, audit, remediation, references
3. ✅ Automatically determines control type (KernelModule, MountPoint, SysctlParameter, etc.)
4. ✅ Adds type-specific parameters
5. ✅ Determines severity level
6. ✅ **Automatically routes controls to correct milestone file** (1.1 → milestone-1-1.json, 2.1 → milestone-2-1.json)
7. ✅ Creates new milestone files if they don't exist
8. ✅ Sorts controls by ID
9. ✅ Shows progress and statistics

**Milestone File Organization:**
- Section 1.1 controls → `/rhel-8/milestones/milestone-1-1.json`
- Section 1.2 controls → `/rhel-8/milestones/milestone-1-2.json`
- Section 2.1 controls → `/rhel-8/milestones/milestone-2-1.json`
- Section 3.3 controls → `/rhel-8/milestones/milestone-3-3.json`
- Section 4.1.1 controls → `/rhel-8/milestones/milestone-4-1-1.json`
- etc.

### MANUAL METHOD (Legacy)

### Step 1: User Provides CIS Documentation
User copy-pastes 5 controls at a time from official CIS RHEL 8 Benchmark v4.0.0 PDF

### Step 2: AI Extracts Information
Extract these fields from CIS documentation:
- Control ID (e.g., 1.1.2.3.1)
- Title
- Description
- Rationale
- Remediation commands
- Impact statement (especially for Level 2)
- References (NIST mappings)
- Severity level
- Profile Level (1 or 2)
- Audit command

### Step 3: Determine Control Type
Map the control to existing or new control type:
- Kernel module checks → KernelModule
- Partition checks → MountPoint
- Mount option checks → MountOption
- Service checks → ServiceStatus
- Package checks → PackageInstalled
- Sysctl checks → SysctlParameter
- File permission checks → FilePermissions
- SSH config checks → SSHConfig
- etc.

### Step 4: Add to Correct Milestone File
Use fsReplace to add the 5 controls to the appropriate milestone JSON file based on section

### Step 5: Implement New Control Types (if needed)
If new control type is needed, add to vijenex-cis.py:
1. Add check function (e.g., check_sysctl_parameter)
2. Update control_type_map dictionary
3. Test the implementation

### Step 6: Verify Automation
- Ensure "automated": true unless CIS doc says "Manual"
- Verify audit command works correctly
- Check that control type properly implements the check

## HTML REPORT FEATURES (BETTER THAN OPENSCAP)

Our HTML reports include:
1. **Professional Styling** - Modern, clean design with color coding
2. **Expandable Controls** - Click to show/hide full details
3. **Severity Breakdown** - Visual chart showing Critical/High/Medium/Low counts
4. **Compliance Scoring** - Percentage-based scoring with color indicators
5. **System Information** - Hostname, OS, kernel, scan timestamp
6. **Impact Warnings** - ⚠️ symbols for Level 2 controls with potential impact
7. **Full CIS Documentation** - Description, rationale, remediation, references
8. **Status Color Coding** - Green (Pass), Red (Fail), Yellow (Manual)
9. **Responsive Design** - Works on all screen sizes

## IMPORTANT NOTES

### Level 2 Controls - ALWAYS Include Impact Warnings
Level 2 controls can break applications. Examples:
- **overlay module**: Breaks Docker/Kubernetes containers
- **udf module**: Required for Azure VM provisioning
- **usb-storage**: Breaks USB device functionality
- **/home noexec**: Breaks user scripts and applications

### Automation Philosophy
- If CIS provides an audit command → AUTOMATE IT
- If check can be scripted → AUTOMATE IT
- Only mark "Manual" if CIS doc explicitly says so (e.g., "Review policy document")

### Testing Strategy
After adding controls:
1. Run scanner: `sudo python3 vijenex-cis.py`
2. Check HTML report in `/tmp/cis_report_*.html`
3. Verify control counts match expectations
4. Ensure no Python errors

## CURRENT STATUS

### Completed
✅ 104+ controls implemented across multiple sections
✅ Automated control extraction script (auto-add-controls.py)
✅ Multiple control types working (KernelModule, MountPoint, MountOption, ServiceStatus, PackageInstalled, SysctlParameter, FileContent)
✅ Professional HTML report generation
✅ Full CIS v4.0.0 documentation in JSON
✅ Automatic milestone file organization by section

### In Progress
🔄 Adding controls in batches of 10-20 using automation script
🔄 Currently covering Sections 1-3 (Filesystem, Services, Network)

### Next Steps
📋 Continue running auto-add-controls.py to reach 256+ controls
📋 Implement remaining control types as needed (FilePermissions, SSHConfig, PAMConfig, AuditRules)
📋 Update vijenex-cis.py to load all milestone files
📋 Test on 50 RHEL 8 machines
📋 Generate consolidated audit report

## QUICK REFERENCE COMMANDS

### Add Controls Automatically (RECOMMENDED)
```bash
cd /Users/satish.korra/Desktop/Linux-CIS-Audit-code/rhel-8/scripts

# Add 10 controls starting from specific ID
python3 auto-add-controls.py --start 1.3.1.1 --count 10

# Add 20 controls from Section 2
python3 auto-add-controls.py --start 2.1.1 --count 20

# Add 15 controls from Section 3
python3 auto-add-controls.py --start 3.1.1 --count 15
```

### Run Scanner (IMPORTANT - USE WRAPPER SCRIPT)
```bash
# CORRECT WAY - Use scan.sh wrapper (auto-detects Python/Go)
cd /Users/satish.korra/Desktop/Linux-CIS-Audit-code/rhel-8
sudo ./scan.sh

# Level 2 scan
sudo ./scan.sh --profile Level2

# Or run Python directly (if needed)
cd /Users/satish.korra/Desktop/Linux-CIS-Audit-code/rhel-8/scripts
sudo python3 vijenex-cis.py --profile Level1
```

### CRITICAL: scan.sh Wrapper Script
**Location**: `/rhel-8/scan.sh`

**What it does:**
1. Checks if running as root
2. Auto-detects Python 3.6+ (preferred)
3. Falls back to Go binary if Python not found
4. Runs the scanner with proper arguments
5. Shows colored output and report location

**Usage on RHEL 8 machine:**
```bash
cd linux-cis-scanner/rhel-8
sudo ./scan.sh
```

### View Report
```bash
# Reports are in rhel-8/reports/ directory
cd /Users/satish.korra/Desktop/Linux-CIS-Audit-code/rhel-8

# HTML report (recommended)
firefox reports/vijenex-cis-report.html

# CSV report
cat reports/vijenex-cis-results.csv
```

### Check Control Count (Single Milestone)
```bash
cd /Users/satish.korra/Desktop/Linux-CIS-Audit-code/rhel-8/milestones
python3 -c "import json; data=json.load(open('milestone-1-1.json')); print(f'Total: {len(data[\"controls\"])}, Automated: {sum(1 for c in data[\"controls\"] if c[\"automated\"])}, Manual: {sum(1 for c in data[\"controls\"] if not c[\"automated\"])}')"
```

### Check Total Control Count (All Milestones)
```bash
cd /Users/satish.korra/Desktop/Linux-CIS-Audit-code/rhel-8/milestones
python3 -c "import json, glob; files=glob.glob('milestone-*.json'); total=0; auto=0; manual=0; [total:=total+len((d:=json.load(open(f)))['controls']) or auto:=auto+sum(1 for c in d['controls'] if c['automated']) or manual:=manual+sum(1 for c in d['controls'] if not c['automated']) for f in files]; print(f'Total: {total}, Automated: {auto}, Manual: {manual}')"
```

## COMPARISON WITH OPENSCAP

### OpenSCAP Results
- Total Automated: 256 controls
- Passed: 152
- Failed: 104
- Manual: Unknown (but minimal)

### Vijenex Initial Results (BAD)
- Total Automated: 73 controls
- Passed: 46
- Failed: 27
- Manual: 191 (TOO MANY!)

### Vijenex Target
- Total Automated: 256+ controls (match or exceed OpenSCAP)
- Manual: Only when CIS explicitly requires manual review
- HTML Report: Better design and usability than OpenSCAP

## WHEN CONTEXT IS LOST

If AI context is lost or backend changes:

1. **Read this file first**: `/Users/satish.korra/Desktop/Linux-CIS-Audit-code/INSTRUCTIONS.md`
2. **Check current progress**: Read `/Users/satish.korra/Desktop/Linux-CIS-Audit-code/rhel-8/milestones/milestone-1-1.json`
3. **Review scanner code**: Read `/Users/satish.korra/Desktop/Linux-CIS-Audit-code/rhel-8/scripts/vijenex-cis.py`
4. **Understand the workflow**: User provides 5 CIS controls → AI extracts info → AI adds to JSON → AI implements new types if needed
5. **Continue from where we left**: Check the last control ID in milestone-1-1.json and continue from next control

## KEY SUCCESS METRICS

1. ✅ Automation Rate: 256+ controls automated (match OpenSCAP)
2. ✅ HTML Report Quality: Better than OpenSCAP
3. ✅ Accuracy: 100% match with CIS v4.0.0 documentation
4. ✅ Completeness: All control fields populated (description, rationale, remediation, impact, references)
5. ✅ Deadline: Complete in 2 days for 50 machine scan

---

**Last Updated**: Current session
**Current Control Count**: 104+ controls across multiple milestone files
**Automation**: Use `python3 auto-add-controls.py --start <ID> --count <N>` to add controls automatically
