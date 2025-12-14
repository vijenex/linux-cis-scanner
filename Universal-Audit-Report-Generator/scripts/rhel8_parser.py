#!/usr/bin/env python3
"""Parse CIS RHEL-8 Benchmark RTF and extract control details"""
import re
from striprtf.striprtf import rtf_to_text

def parse_cis_benchmark(rtf_path):
    """Extract control ID, title, description, impact, remediation from CIS RTF"""
    with open(rtf_path, 'r', encoding='utf-8', errors='ignore') as f:
        text = rtf_to_text(f.read())
    
    controls = {}
    lines = [l.strip() for l in text.split('\n') if l.strip()]
    
    i = 0
    while i < len(lines):
        line = lines[i]
        
        # Match control ID pattern: 1.1.1.1 Ensure...
        match = re.match(r'^(\d+\.\d+\.\d+(?:\.\d+)?)\s+(Ensure|Configure|Install|Set|Verify|Record|Disable|Enable|Remove|Restrict|Require|Audit|Check|Lock|Limit|Add|Create|Modify|Update)\s+(.*)', line, re.IGNORECASE)
        if match:
            control_id = match.group(1)
            title = match.group(2) + ' ' + match.group(3)
            title = re.sub(r'\s+\((Automated|Manual)\)$', '', title).strip()
            
            description = ''
            impact = ''
            remediation = ''
            section = None
            
            # Parse next lines for details
            for j in range(i+1, min(i+100, len(lines))):
                curr_line = lines[j]
                
                # Stop at next control
                if re.match(r'^\d+\.\d+(?:\.\d+)*(?:\.\d+)?', curr_line):
                    break
                
                # Identify sections
                if 'Description:' in curr_line or 'Rationale:' in curr_line:
                    section = 'description'
                elif 'Impact:' in curr_line:
                    section = 'impact'
                elif 'Remediation:' in curr_line:
                    section = 'remediation'
                elif 'Audit:' in curr_line or 'Default Value:' in curr_line or 'References:' in curr_line:
                    section = None
                elif section and curr_line:
                    if section == 'description':
                        description += curr_line + ' '
                    elif section == 'impact':
                        impact += curr_line + ' '
                    elif section == 'remediation':
                        remediation += curr_line + ' '
            
            controls[control_id] = {
                'id': control_id,
                'title': title,
                'description': description.strip(),
                'impact': impact.strip(),
                'remediation': remediation.strip()
            }
        
        i += 1
    
    return controls

if __name__ == '__main__':
    rtf_path = '../cis-benchmarks/rhel-8/CIS_Red_Hat_Enterprise_Linux_8_Benchmark_v4.0.0.txt.rtf'
    controls = parse_cis_benchmark(rtf_path)
    print(f"Parsed {len(controls)} controls from CIS benchmark")
    
    # Show sample
    for i, (cid, data) in enumerate(list(controls.items())[:3]):
        print(f"\n{cid}: {data['title'][:60]}")
        print(f"  Description: {data['description'][:80]}...")
