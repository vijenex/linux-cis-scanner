#!/usr/bin/env python3
"""
Reorganize controls from milestone-1-1.json into correct milestone files
"""

import json
from pathlib import Path
from collections import defaultdict

MILESTONE_DIR = Path("/Users/satish.korra/Desktop/Linux-CIS-Audit-code/rhel-8/milestones")
SOURCE_FILE = MILESTONE_DIR / "milestone-1-1.json"

def get_milestone_name(control_id):
    """Get milestone filename for a control ID"""
    parts = control_id.split('.')
    return f"milestone-{parts[0]}-{parts[1]}.json"

def main():
    print("🔄 Reorganizing controls into correct milestone files...\n")
    
    # Read all controls from milestone-1-1.json
    with open(SOURCE_FILE, 'r') as f:
        data = json.load(f)
    
    all_controls = data['controls']
    print(f"📦 Found {len(all_controls)} controls in milestone-1-1.json")
    
    # Group controls by milestone file
    controls_by_milestone = defaultdict(list)
    for control in all_controls:
        milestone_file = get_milestone_name(control['id'])
        controls_by_milestone[milestone_file].append(control)
    
    print(f"📂 Will distribute across {len(controls_by_milestone)} milestone files\n")
    
    # Write to appropriate milestone files
    for milestone_file, controls in sorted(controls_by_milestone.items()):
        milestone_path = MILESTONE_DIR / milestone_file
        section = milestone_file.replace('milestone-', '').replace('.json', '').replace('-', '.')
        
        # Sort controls by ID
        controls.sort(key=lambda x: [int(p) for p in x['id'].split('.')])
        
        # Create milestone data
        milestone_data = {
            "milestone": section,
            "version": "1.0.0",
            "description": f"RHEL 8 CIS Benchmark v4.0.0 - Section {section}",
            "controls": controls
        }
        
        # Write to file
        with open(milestone_path, 'w') as f:
            json.dump(milestone_data, f, indent=2)
        
        automated = sum(1 for c in controls if c['automated'])
        manual = len(controls) - automated
        print(f"✅ {milestone_file}: {len(controls)} controls ({automated} automated, {manual} manual)")
    
    # Keep only Section 1.1 controls in milestone-1-1.json
    section_1_1_controls = [c for c in all_controls if c['id'].startswith('1.1.')]
    section_1_1_controls.sort(key=lambda x: [int(p) for p in x['id'].split('.')])
    
    data['controls'] = section_1_1_controls
    data['milestone'] = "1.1"
    data['description'] = "RHEL 8 CIS Benchmark v4.0.0 - Section 1.1 Filesystem Configuration"
    
    with open(SOURCE_FILE, 'w') as f:
        json.dump(data, f, indent=2)
    
    print(f"\n✅ milestone-1-1.json updated: {len(section_1_1_controls)} controls (Section 1.1 only)")
    print("\n🎉 Reorganization complete!")

if __name__ == "__main__":
    main()
