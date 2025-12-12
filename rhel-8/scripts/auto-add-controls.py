#!/usr/bin/env python3
"""
Automated CIS Control Extractor - Reads CIS RTF and adds controls to JSON
Usage: python3 auto-add-controls.py --start 1.3.1.1 --count 10
"""

import json
import re
import sys
from pathlib import Path

CIS_DOC = "/Users/satish.korra/Desktop/CIS-controls-list/CIS_Red_Hat_Enterprise_Linux_8_Benchmark_v4.0.0.txt.rtf"
MILESTONE_DIR = "/Users/satish.korra/Desktop/Linux-CIS-Audit-code/rhel-8/milestones"

def read_cis_document():
    """Read CIS RTF document"""
    try:
        with open(CIS_DOC, 'r', encoding='utf-8', errors='ignore') as f:
            return f.read()
    except Exception as e:
        print(f"Error reading CIS document: {e}")
        return None

def extract_next_controls(cis_text, start_id, count=10):
    """Extract next N controls starting from start_id"""
    controls = []
    
    # Split by control ID pattern
    pattern = r'(\d+\.\d+\.\d+(?:\.\d+)?(?:\.\d+)?)\s+Ensure'
    matches = list(re.finditer(pattern, cis_text))
    
    # Find starting position
    start_idx = None
    for i, match in enumerate(matches):
        if match.group(1) == start_id:
            start_idx = i
            break
    
    if start_idx is None:
        print(f"Control {start_id} not found in document")
        return controls
    
    # Extract next 'count' controls
    for i in range(start_idx, min(start_idx + count, len(matches))):
        control_start = matches[i].start()
        control_end = matches[i+1].start() if i+1 < len(matches) else len(cis_text)
        control_text = cis_text[control_start:control_end]
        
        control = parse_control(control_text)
        if control:
            controls.append(control)
    
    return controls

def parse_control(text):
    """Parse a single control from text"""
    control = {}
    
    # Extract ID and Title
    id_title = re.search(r'(\d+\.\d+\.\d+(?:\.\d+)?(?:\.\d+)?)\s+Ensure\s+(.+?)\s*\(', text)
    if not id_title:
        return None
    
    control['id'] = id_title.group(1)
    control['title'] = f"Ensure {id_title.group(2).strip()}"
    
    # Automated or Manual
    control['automated'] = '(Automated)' in text[:500]
    
    # Profile Level
    if 'Level 2' in text[:1000]:
        control['profile'] = 'Level2'
    else:
        control['profile'] = 'Level1'
    
    # Section (derive from ID)
    parts = control['id'].split('.')
    if len(parts) >= 2:
        control['section'] = f"{parts[0]}.{parts[1]}"
    
    # Description
    desc = re.search(r'Description[:\s]+(.+?)(?=Rationale|$)', text, re.DOTALL | re.IGNORECASE)
    control['description'] = desc.group(1).strip()[:500] if desc else "No description"
    
    # Rationale
    rat = re.search(r'Rationale[:\s]+(.+?)(?=Impact|Audit|$)', text, re.DOTALL | re.IGNORECASE)
    control['rationale'] = rat.group(1).strip()[:500] if rat else "No rationale"
    
    # Impact
    imp = re.search(r'Impact[:\s]+(.+?)(?=Audit|Remediation|$)', text, re.DOTALL | re.IGNORECASE)
    control['impact'] = imp.group(1).strip()[:300] if imp else "None"
    
    # Audit
    aud = re.search(r'Audit[:\s]+(.+?)(?=Remediation|$)', text, re.DOTALL | re.IGNORECASE)
    control['audit_command'] = aud.group(1).strip()[:500] if aud else ""
    
    # Remediation
    rem = re.search(r'Remediation[:\s]+(.+?)(?=References|Default|Additional|$)', text, re.DOTALL | re.IGNORECASE)
    control['remediation'] = rem.group(1).strip()[:800] if rem else ""
    
    # References
    ref = re.search(r'References[:\s]+(.+?)(?=CIS Controls|Additional|$)', text, re.DOTALL | re.IGNORECASE)
    control['references'] = ref.group(1).strip()[:300] if ref else ""
    
    # Determine control type and add parameters
    control_type = determine_type(control)
    control['type'] = control_type
    add_parameters(control, control_type)
    
    # Severity
    control['severity'] = determine_severity(control)
    
    # CIS Reference
    control['cis_reference'] = f"CIS RHEL 8 v4.0.0 - {control['id']} | {control['profile']}"
    
    return control

def determine_type(control):
    """Determine control type"""
    title = control['title'].lower()
    audit = control.get('audit_command', '').lower()
    
    if not control['automated']:
        return 'Manual'
    
    if 'kernel module' in title or 'lsmod' in audit:
        return 'KernelModule'
    if 'separate partition' in title:
        return 'MountPoint'
    if any(x in title for x in ['nodev', 'nosuid', 'noexec']) and 'findmnt' in audit:
        return 'MountOption'
    if 'sysctl' in audit:
        return 'SysctlParameter'
    if 'systemctl' in audit and 'is-enabled' in audit:
        return 'ServiceStatus'
    if 'rpm -q' in audit or 'dnf list' in audit:
        return 'PackageInstalled'
    if 'grep' in audit and '/etc/' in audit:
        return 'FileContent'
    if any(x in audit for x in ['stat', 'ls -l', 'find']) and 'perm' in audit:
        return 'FilePermissions'
    if 'sshd_config' in audit:
        return 'SSHConfig'
    
    return 'FileContent'  # Default

def add_parameters(control, ctype):
    """Add type-specific parameters"""
    title = control['title'].lower()
    audit = control.get('audit_command', '')
    
    if ctype == 'MountPoint':
        for mp in ['/tmp', '/dev/shm', '/home', '/var', '/var/tmp', '/var/log', '/var/log/audit']:
            if mp in title:
                control['mount_point'] = mp
                control['expected_status'] = 'separate_partition'
                break
    
    elif ctype == 'MountOption':
        for mp in ['/tmp', '/dev/shm', '/home', '/var', '/var/tmp', '/var/log', '/var/log/audit']:
            if mp in title:
                control['mount_point'] = mp
                break
        for opt in ['nodev', 'nosuid', 'noexec']:
            if opt in title:
                control['required_option'] = opt
                break
    
    elif ctype == 'FileContent':
        file_match = re.search(r'(/etc/[^\s]+)', audit)
        if file_match:
            control['file_path'] = file_match.group(1)
        control['pattern'] = ''
        control['expected_result'] = 'found'

def determine_severity(control):
    """Determine severity based on profile and type"""
    if control['profile'] == 'Level2':
        return 'medium'
    if 'gpgcheck' in control['title'].lower():
        return 'critical'
    if 'password' in control['title'].lower() or 'authentication' in control['title'].lower():
        return 'high'
    return 'medium'

def get_milestone_file(control_id):
    """Determine milestone file based on control ID"""
    parts = control_id.split('.')
    
    # For controls like 1.1.1.1 -> milestone-1-1.json
    # For controls like 4.1.1.1 -> milestone-4-1-1.json
    if len(parts) >= 3:
        if parts[0] in ['4', '5']:
            # Check if 4-1-1 pattern exists
            milestone_file = f"{MILESTONE_DIR}/milestone-{parts[0]}-{parts[1]}-{parts[2]}.json"
            if Path(milestone_file).exists():
                return milestone_file
        
        # Default: use first two parts (e.g., 1.1, 2.1, 3.3)
        milestone_file = f"{MILESTONE_DIR}/milestone-{parts[0]}-{parts[1]}.json"
        return milestone_file
    
    return f"{MILESTONE_DIR}/milestone-{parts[0]}-{parts[1]}.json"

def add_to_milestone(controls):
    """Add controls to appropriate milestone JSON files"""
    # Group controls by milestone file
    controls_by_milestone = {}
    
    for control in controls:
        milestone_file = get_milestone_file(control['id'])
        if milestone_file not in controls_by_milestone:
            controls_by_milestone[milestone_file] = []
        controls_by_milestone[milestone_file].append(control)
    
    # Process each milestone file
    total_added = 0
    for milestone_file, milestone_controls in controls_by_milestone.items():
        milestone_name = Path(milestone_file).stem
        print(f"\n📁 Processing {milestone_name}...")
        
        # Create file if it doesn't exist
        if not Path(milestone_file).exists():
            section = milestone_name.replace('milestone-', '').replace('-', '.')
            data = {
                "milestone": section,
                "version": "1.0.0",
                "description": f"RHEL 8 CIS Benchmark v4.0.0 - Section {section}",
                "controls": []
            }
            print(f"   ✨ Created new milestone file: {milestone_name}")
        else:
            with open(milestone_file, 'r') as f:
                data = json.load(f)
        
        existing_ids = {c.get('id', c.get('control_id', '')) for c in data['controls'] if isinstance(c, dict)}
        
        for control in milestone_controls:
            if control['id'] not in existing_ids:
                data['controls'].append(control)
                print(f"   ✅ Added: {control['id']} - {control['title']}")
                total_added += 1
            else:
                print(f"   ⚠️  Skipped (exists): {control['id']}")
        
        # Sort by ID (handle both 'id' and 'control_id' fields)
        data['controls'].sort(key=lambda x: [int(p) for p in x.get('id', x.get('control_id', '0.0')).split('.')])
        
        with open(milestone_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"   📊 {milestone_name}: {len(data['controls'])} controls ({sum(1 for c in data['controls'] if c.get('automated', False))} automated)")
    
    print(f"\n🎉 Total added: {total_added} controls")

def main():
    if len(sys.argv) < 3:
        print("Usage: python3 auto-add-controls.py --start 1.3.1.1 --count 10")
        sys.exit(1)
    
    start_id = sys.argv[2]
    count = int(sys.argv[4]) if len(sys.argv) > 4 else 10
    
    print(f"🔍 Reading CIS document...")
    cis_text = read_cis_document()
    if not cis_text:
        sys.exit(1)
    
    print(f"📝 Extracting {count} controls starting from {start_id}...")
    controls = extract_next_controls(cis_text, start_id, count)
    
    if not controls:
        print("❌ No controls extracted")
        sys.exit(1)
    
    print(f"\n✨ Extracted {len(controls)} controls")
    add_to_milestone(controls)

if __name__ == "__main__":
    main()
