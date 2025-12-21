#!/usr/bin/env python3
"""
Update Ubuntu milestone files with description and remediation from official CIS documents.
Extracts description and remediation steps from PDF/RTF files and updates milestone JSON files.

Usage:
    python3 update-ubuntu-milestones.py <cis_document> <milestones_dir> <ubuntu_version>
    
Example:
    python3 update-ubuntu-milestones.py ~/Downloads/CIS_Ubuntu_22.04_Benchmark.pdf ubuntu-22.04/go-scanner/milestones 22.04
"""

import json
import re
import os
import sys
from pathlib import Path

try:
    import PyPDF2
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False
    print("⚠️  PyPDF2 not installed. Install with: pip install PyPDF2")

def extract_text_from_pdf(pdf_path):
    """Extract text from PDF file"""
    if not PDF_AVAILABLE:
        raise ImportError("PyPDF2 is required for PDF parsing. Install with: pip install PyPDF2")
    
    text = ""
    with open(pdf_path, 'rb') as f:
        pdf = PyPDF2.PdfReader(f)
        for page in pdf.pages:
            text += page.extract_text() + "\n"
    return text

def extract_text_from_rtf(rtf_path):
    """Extract text from RTF file"""
    try:
        from striprtf.striprtf import rtf_to_text
        with open(rtf_path, 'r', encoding='utf-8', errors='ignore') as f:
            return rtf_to_text(f.read())
    except ImportError:
        # Fallback: basic RTF stripping
        with open(rtf_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            # Remove RTF formatting codes
            content = re.sub(r'\\[a-z]+\d*\s?', ' ', content)
            content = re.sub(r'[{}]', '', content)
            content = re.sub(r'\s+', ' ', content)
            return content

def extract_control_sections(text, control_id):
    """Extract description and remediation for a specific control ID"""
    # Pattern to find control section
    # Match: 1.1.1.1 (L1) or 1.1.1.1 Ensure...
    pattern = rf'({re.escape(control_id)}\s*(?:\(L\d\)|Ensure|Configure|Install|Set|Verify|Record|Disable|Enable|Remove|Restrict|Require|Audit|Check|Lock|Limit|Add|Create|Modify|Update))'
    
    match = re.search(pattern, text, re.IGNORECASE)
    if not match:
        return None, None
    
    # Find the end of this control (next control ID or end of text)
    start_pos = match.start()
    
    # Find next control ID
    next_pattern = r'(\d+\.\d+\.\d+(?:\.\d+)*)\s*(?:\(L\d\)|Ensure|Configure|Install|Set|Verify|Record|Disable|Enable|Remove|Restrict|Require|Audit|Check|Lock|Limit|Add|Create|Modify|Update)'
    next_match = re.search(next_pattern, text[start_pos + 100:], re.IGNORECASE)
    end_pos = start_pos + 100 + next_match.start() if next_match else len(text)
    
    control_text = text[start_pos:end_pos]
    
    # Extract Description
    description = None
    desc_patterns = [
        r'Description:\s*(.*?)(?=Rationale:|Impact:|Audit:|Remediation:|References:|CIS Controls:|$)',
        r'Description\s*(?:\(L\d\))?:\s*(.*?)(?=Rationale:|Impact:|Audit:|Remediation:|References:|CIS Controls:|$)',
    ]
    for pattern in desc_patterns:
        match = re.search(pattern, control_text, re.DOTALL | re.IGNORECASE)
        if match:
            description = match.group(1).strip()
            # Clean up description
            description = re.sub(r'\s+', ' ', description)
            description = description[:1000]  # Limit length
            break
    
    # Extract Remediation
    remediation = None
    rem_patterns = [
        r'Remediation:\s*(.*?)(?=References:|Impact:|CIS Controls:|Audit:|$)',
        r'Remediation\s*(?:\(L\d\))?:\s*(.*?)(?=References:|Impact:|CIS Controls:|Audit:|$)',
    ]
    for pattern in rem_patterns:
        match = re.search(pattern, control_text, re.DOTALL | re.IGNORECASE)
        if match:
            remediation = match.group(1).strip()
            # Clean up remediation
            remediation = re.sub(r'\s+', ' ', remediation)
            # Remove RTF/PDF artifacts
            remediation = re.sub(r'\\[a-z]+\d*\s?', '', remediation)
            remediation = remediation[:2000]  # Limit length
            break
    
    return description, remediation

def update_milestone_file(milestone_path, cis_text):
    """Update a milestone file with description and remediation"""
    with open(milestone_path, 'r') as f:
        data = json.load(f)
    
    updated_count = 0
    for control in data.get('controls', []):
        control_id = control.get('id', '')
        if not control_id:
            continue
        
        # Extract description and remediation from CIS document
        description, remediation = extract_control_sections(cis_text, control_id)
        
        if description:
            control['description'] = description
            updated_count += 1
        
        if remediation:
            control['remediation'] = remediation
            updated_count += 1
        
        # Remove reference_note if we have actual content
        if description and remediation and 'reference_note' in control:
            # Keep cis_reference but remove reference_note
            if 'reference_note' in control:
                del control['reference_note']
    
    # Write back updated file
    with open(milestone_path, 'w') as f:
        json.dump(data, f, indent=2)
    
    return updated_count

def main():
    if len(sys.argv) < 4:
        print("Usage: python3 update-ubuntu-milestones.py <cis_document> <milestones_dir> <ubuntu_version>")
        print("\nExample:")
        print("  python3 update-ubuntu-milestones.py ~/Downloads/CIS_Ubuntu_22.04_Benchmark.pdf ubuntu-22.04/go-scanner/milestones 22.04")
        sys.exit(1)
    
    cis_doc_path = sys.argv[1]
    milestones_dir = sys.argv[2]
    ubuntu_version = sys.argv[3]
    
    if not os.path.exists(cis_doc_path):
        print(f"❌ CIS document not found: {cis_doc_path}")
        sys.exit(1)
    
    if not os.path.exists(milestones_dir):
        print(f"❌ Milestones directory not found: {milestones_dir}")
        sys.exit(1)
    
    print(f"📄 Reading CIS document: {cis_doc_path}")
    
    # Extract text from document
    if cis_doc_path.lower().endswith('.pdf'):
        if not PDF_AVAILABLE:
            print("❌ PyPDF2 is required for PDF parsing. Install with: pip install PyPDF2")
            sys.exit(1)
        cis_text = extract_text_from_pdf(cis_doc_path)
    elif cis_doc_path.lower().endswith('.rtf'):
        cis_text = extract_text_from_rtf(cis_doc_path)
    else:
        print("❌ Unsupported file format. Please provide PDF or RTF file.")
        sys.exit(1)
    
    print(f"✅ Extracted {len(cis_text)} characters from document")
    
    # Find all milestone files
    milestone_files = sorted(Path(milestones_dir).glob('milestone-*.json'))
    
    if not milestone_files:
        print(f"❌ No milestone files found in {milestones_dir}")
        sys.exit(1)
    
    print(f"📋 Found {len(milestone_files)} milestone files")
    print("\n🔄 Updating milestone files...")
    
    total_updated = 0
    for milestone_file in milestone_files:
        updated = update_milestone_file(milestone_file, cis_text)
        total_updated += updated
        if updated > 0:
            print(f"  ✓ {milestone_file.name}: Updated {updated} fields")
    
    print(f"\n✅ Complete! Updated {total_updated} control fields across {len(milestone_files)} milestone files")
    print(f"\n📝 Note: Controls without description/remediation in the document were left unchanged")

if __name__ == '__main__':
    main()

