#!/usr/bin/env python3
"""
Update milestone files to replace custom descriptions with official CIS benchmark URLs
"""

import json
import os
import glob

def update_milestone_file(filepath, ubuntu_version):
    """Update a single milestone file to use CIS URLs instead of custom descriptions"""
    
    # CIS benchmark URLs for different Ubuntu versions
    cis_urls = {
        "20.04": "https://www.cisecurity.org/benchmark/ubuntu_linux",
        "22.04": "https://www.cisecurity.org/benchmark/ubuntu_linux", 
        "24.04": "https://www.cisecurity.org/benchmark/ubuntu_linux"
    }
    
    base_url = cis_urls.get(ubuntu_version, "https://www.cisecurity.org/benchmark/ubuntu_linux")
    
    with open(filepath, 'r') as f:
        data = json.load(f)
    
    # Update each control
    for control in data.get('controls', []):
        control_id = control.get('id', '')
        
        # Replace description, rationale, impact, remediation with CIS URL reference
        control['cis_reference'] = f"{base_url}"
        control['cis_control_id'] = control_id
        control['reference_note'] = f"For detailed description, rationale, impact assessment, and remediation steps, please refer to the official CIS Ubuntu Linux {ubuntu_version} Benchmark document at the above URL."
        
        # Remove the custom fields to avoid confusion
        fields_to_remove = ['description', 'rationale', 'impact', 'remediation']
        for field in fields_to_remove:
            if field in control:
                del control[field]
    
    # Write back the updated data
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)
    
    print(f"✓ Updated {filepath}")

def main():
    """Update all milestone files"""
    
    # Ubuntu versions to process
    ubuntu_versions = ['20.04', '22.04', '24.04']
    
    for version in ubuntu_versions:
        ubuntu_dir = f"ubuntu-{version}"
        if os.path.exists(ubuntu_dir):
            milestone_pattern = os.path.join(ubuntu_dir, 'milestones', 'milestone-*.json')
            milestone_files = glob.glob(milestone_pattern)
            
            print(f"\n🔄 Processing Ubuntu {version} ({len(milestone_files)} files)...")
            
            for filepath in sorted(milestone_files):
                update_milestone_file(filepath, version)
        else:
            print(f"⚠ Directory {ubuntu_dir} not found, skipping...")
    
    print(f"\n✅ All milestone files updated with CIS benchmark URLs!")
    print("📋 Custom descriptions/remediation removed to prevent incorrect guidance")
    print("🔗 Users should refer to official CIS benchmark documents for accurate information")

if __name__ == "__main__":
    main()