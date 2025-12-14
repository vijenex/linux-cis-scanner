#!/usr/bin/env python3
"""
Enhanced RHEL 8 RTF Parser
Extracts detailed audit information from OpenSCAP RTF output
"""
import re
import os
from striprtf.striprtf import rtf_to_text

def parse_openscap_rtf(rtf_path):
    """Parse OpenSCAP RTF output and extract structured data"""
    if not os.path.exists(rtf_path):
        return {}
    
    try:
        with open(rtf_path, 'r', encoding='utf-8', errors='ignore') as f:
            rtf_content = f.read()
        
        # Convert RTF to plain text
        text_content = rtf_to_text(rtf_content)
        
        # Extract audit results
        results = {
            'server_ip': os.path.basename(rtf_path).replace('.txt.rtf', ''),
            'scan_date': None,
            'total_rules': 0,
            'passed': 0,
            'failed': 0,
            'score': 0.0,
            'failed_controls': {},
            'passed_controls': {}
        }
        
        lines = text_content.split('\n')
        
        # Extract summary information
        for line in lines:
            line = line.strip()
            
            # Extract scores and counts
            if 'passed' in line.lower() and any(char.isdigit() for char in line):
                numbers = re.findall(r'\d+', line)
                if numbers and 'passed' in line.lower():
                    results['passed'] = int(numbers[0])
            
            if 'failed' in line.lower() and any(char.isdigit() for char in line):
                numbers = re.findall(r'\d+', line)
                if numbers and 'failed' in line.lower():
                    results['failed'] = int(numbers[0])
            
            if 'percent' in line.lower() or '%' in line:
                numbers = re.findall(r'\d+\.?\d*', line)
                if numbers:
                    results['score'] = float(numbers[0])
        
        # Extract individual control results
        current_section = None
        for i, line in enumerate(lines):
            line = line.strip()
            
            # Look for control entries with fail status
            if 'fail' in line.lower():
                # Try to extract control ID and title
                control_match = re.search(r'(\d+\.\d+(?:\.\d+)*)', line)
                if control_match:
                    control_id = control_match.group(1)
                    
                    # Extract title (everything after control ID, before severity/status)
                    title_part = line[control_match.end():].strip()
                    title_part = re.sub(r'\b(fail|medium|high|low|critical)\b', '', title_part, flags=re.IGNORECASE).strip()
                    
                    # Extract severity
                    severity = 'medium'  # default
                    if 'high' in line.lower():
                        severity = 'high'
                    elif 'low' in line.lower():
                        severity = 'low'
                    elif 'critical' in line.lower():
                        severity = 'critical'
                    
                    results['failed_controls'][control_id] = {
                        'title': title_part,
                        'severity': severity,
                        'status': 'FAIL'
                    }
            
            # Look for pass entries
            elif 'pass' in line.lower():
                control_match = re.search(r'(\d+\.\d+(?:\.\d+)*)', line)
                if control_match:
                    control_id = control_match.group(1)
                    title_part = line[control_match.end():].strip()
                    title_part = re.sub(r'\b(pass|medium|high|low|critical)\b', '', title_part, flags=re.IGNORECASE).strip()
                    
                    results['passed_controls'][control_id] = {
                        'title': title_part,
                        'status': 'PASS'
                    }
        
        results['total_rules'] = results['passed'] + results['failed']
        
        return results
        
    except Exception as e:
        print(f"Error parsing RTF file {rtf_path}: {e}")
        return {}

def extract_server_ip_from_filename(filename):
    """Extract server IP from filename"""
    # Remove file extensions
    base_name = filename.replace('.txt.rtf', '').replace('.html', '')
    
    # Check if it's an IP address pattern
    ip_pattern = r'\b(?:\d{1,3}\.){3}\d{1,3}\b'
    ip_match = re.search(ip_pattern, base_name)
    
    if ip_match:
        return ip_match.group(0)
    else:
        return base_name

def test_parser():
    """Test the parser with sample data"""
    base_path = "/Users/satish.korra/Downloads/RHEL-8"
    
    # Test UAT servers
    uat_path = os.path.join(base_path, "UAT")
    if os.path.exists(uat_path):
        print("Testing UAT servers:")
        for filename in os.listdir(uat_path):
            if filename.endswith('.txt.rtf'):
                file_path = os.path.join(uat_path, filename)
                results = parse_openscap_rtf(file_path)
                print(f"  {filename}: {results['failed']} failed, {results['passed']} passed, Score: {results['score']}%")
                
                # Show first few failed controls
                if results['failed_controls']:
                    print("    Failed controls:")
                    for i, (control_id, control_data) in enumerate(list(results['failed_controls'].items())[:3]):
                        print(f"      {control_id}: {control_data['title'][:50]}...")
                print()

if __name__ == '__main__':
    test_parser()