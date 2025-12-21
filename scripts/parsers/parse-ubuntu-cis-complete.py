#!/usr/bin/env python3
"""
Complete parser for Ubuntu CIS Benchmark documents.
Extracts FULL descriptions and remediation steps with proper formatting (no breaks).

Usage:
    python3 parse-ubuntu-cis-complete.py <cis_document> <milestones_dir> <ubuntu_version>
    
Example:
    python3 parse-ubuntu-cis-complete.py ~/Downloads/CIS_Ubuntu_22.04_Benchmark.pdf ubuntu-22.04/go-scanner/milestones 22.04
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

try:
    from striprtf.striprtf import rtf_to_text
    RTF_AVAILABLE = True
except ImportError:
    RTF_AVAILABLE = False

def extract_text_from_pdf(pdf_path):
    """Extract text from PDF file with better formatting"""
    if not PDF_AVAILABLE:
        raise ImportError("PyPDF2 is required for PDF parsing. Install with: pip install PyPDF2")
    
    text = ""
    with open(pdf_path, 'rb') as f:
        pdf = PyPDF2.PdfReader(f)
        print(f"   📄 Document has {len(pdf.pages)} pages")
        for page_num, page in enumerate(pdf.pages):
            page_text = page.extract_text()
            text += page_text + "\n"
            if (page_num + 1) % 50 == 0:
                print(f"   📄 Processed {page_num + 1} pages...")
    return text

def extract_text_from_rtf(rtf_path):
    """Extract text from RTF file"""
    if RTF_AVAILABLE:
        with open(rtf_path, 'r', encoding='utf-8', errors='ignore') as f:
            return rtf_to_text(f.read())
    else:
        # Fallback: basic RTF stripping
        with open(rtf_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            # Remove RTF formatting codes
            content = re.sub(r'\\[a-z]+\d*\s?', ' ', content)
            content = re.sub(r'[{}]', '', content)
            return content

def normalize_control_id(control_id):
    """Normalize control ID for matching"""
    return control_id.strip().rstrip('.')

def find_control_section(text, control_id):
    """Find the complete section for a control ID in actual content (not TOC)"""
    normalized_id = normalize_control_id(control_id)
    
    # Find all occurrences of this control ID
    # Pattern to match control ID followed by title
    base_pattern = rf'{re.escape(normalized_id)}\s+(?:Ensure|Configure|Install|Set|Verify|Record|Disable|Enable|Remove|Restrict|Require|Audit|Check|Lock|Limit|Add|Create|Modify|Update)'
    
    # Find all matches
    matches = list(re.finditer(base_pattern, text, re.IGNORECASE | re.MULTILINE))
    
    if not matches:
        return None
    
    # Find the match that has actual content (Description or Profile Applicability nearby)
    # This distinguishes content sections from TOC entries
    for match in matches:
        start_pos = match.start()
        # Check next 2000 chars for content markers
        check_text = text[start_pos:start_pos + 2000]
        
        # If this section has Description or Profile Applicability, it's actual content
        if 'Description:' in check_text or 'Profile Applicability:' in check_text:
            # Found actual content section
            # Now find where this control ends (next control with content)
            # Look for next control ID that also has Description/Profile
            next_pattern = r'(\d+\.\d+(?:\.\d+)*(?:\.\d+)?)\s+(?:Ensure|Configure|Install|Set|Verify|Record|Disable|Enable|Remove|Restrict|Require|Audit|Check|Lock|Limit|Add|Create|Modify|Update)'
            
            # Search for next control starting well after current one
            search_start = start_pos + 500
            next_matches = list(re.finditer(next_pattern, text[search_start:], re.IGNORECASE | re.MULTILINE))
            
            end_pos = None
            for next_match in next_matches:
                next_check_start = search_start + next_match.start()
                next_check_text = text[next_check_start:next_check_start + 2000]
                # If next control also has content markers, that's our boundary
                if 'Description:' in next_check_text or 'Profile Applicability:' in next_check_text:
                    end_pos = next_check_start
                    break
            
            if end_pos is None:
                # No next control found, take large chunk
                end_pos = min(start_pos + 20000, len(text))
            
            control_text = text[start_pos:end_pos]
            return control_text
    
    # No content section found
    return None

def extract_description(control_text):
    """Extract complete description section - preserve formatting"""
    # Multiple patterns to find Description section
    desc_patterns = [
        # Pattern 1: Description: ... (until next section) - use DOTALL to match across lines
        r'Description:\s*(.*?)(?=(?:Rationale|Impact|Audit|Remediation|References|CIS Controls|Default Value|Profile Applicability|^\d+\.\d+\.\d+):)',
        # Pattern 2: Description (L1): ... 
        r'Description\s*\(L\d\):\s*(.*?)(?=(?:Rationale|Impact|Audit|Remediation|References|CIS Controls|Default Value|Profile Applicability|^\d+\.\d+\.\d+):)',
        # Pattern 3: Description : ... (with space)
        r'Description\s*:\s*(.*?)(?=(?:Rationale|Impact|Audit|Remediation|References|CIS Controls|Default Value|Profile Applicability|^\d+\.\d+\.\d+):)',
    ]
    
    for pattern in desc_patterns:
        match = re.search(pattern, control_text, re.DOTALL | re.IGNORECASE | re.MULTILINE)
        if match:
            description = match.group(1)
            
            # Clean up but preserve line breaks and structure
            # Remove RTF/PDF artifacts
            description = re.sub(r'\\[a-z]+\d*\s?', '', description)
            description = re.sub(r'[{}]', '', description)
            
            # Normalize whitespace but keep paragraph structure
            # Replace multiple spaces with single space
            description = re.sub(r'[ \t]+', ' ', description)
            # Replace multiple newlines (3+) with double newline (paragraph break)
            description = re.sub(r'\n\s*\n\s*\n+', '\n\n', description)
            # Clean up single newlines within paragraphs (join lines)
            lines = description.split('\n')
            cleaned_lines = []
            for line in lines:
                line = line.strip()
                if line:
                    # If line doesn't end with punctuation and next line exists, join them
                    if cleaned_lines and not cleaned_lines[-1].rstrip().endswith(('.', '!', '?', ':', ';')):
                        cleaned_lines[-1] += ' ' + line
                    else:
                        cleaned_lines.append(line)
            
            description = '\n'.join(cleaned_lines)
            description = description.strip()
            
            # Remove any remaining artifacts
            description = re.sub(r'Page \d+', '', description, flags=re.IGNORECASE)
            description = re.sub(r'---PAGE \d+---', '', description)
            
            return description if description else None
    
    return None

def extract_remediation(control_text):
    """Extract complete remediation section - preserve command formatting"""
    # Multiple patterns to find Remediation section
    rem_patterns = [
        # Pattern 1: Remediation: ... (until next section or next control) - use DOTALL
        r'Remediation:\s*(.*?)(?=(?:References|Impact|CIS Controls|Audit|Default Value|Description|Rationale|Profile Applicability|^\d+\.\d+\.\d+):)',
        # Pattern 2: Remediation (L1): ...
        r'Remediation\s*\(L\d\):\s*(.*?)(?=(?:References|Impact|CIS Controls|Audit|Default Value|Description|Rationale|Profile Applicability|^\d+\.\d+\.\d+):)',
        # Pattern 3: Remediation : ... (with space)
        r'Remediation\s*:\s*(.*?)(?=(?:References|Impact|CIS Controls|Audit|Default Value|Description|Rationale|Profile Applicability|^\d+\.\d+\.\d+):)',
    ]
    
    for pattern in rem_patterns:
        match = re.search(pattern, control_text, re.DOTALL | re.IGNORECASE | re.MULTILINE)
        if match:
            remediation = match.group(1)
            
            # Clean up but preserve command formatting
            # Remove RTF/PDF artifacts
            remediation = re.sub(r'\\[a-z]+\d*\s?', '', remediation)
            remediation = re.sub(r'[{}]', '', remediation)
            
            # Preserve line breaks for commands (lines starting with #, $, or commands)
            # Normalize whitespace
            remediation = re.sub(r'[ \t]+', ' ', remediation)
            
            # Clean up multiple newlines but preserve structure
            remediation = re.sub(r'\n\s*\n\s*\n+', '\n\n', remediation)
            
            # Remove page markers and artifacts
            remediation = re.sub(r'Page \d+', '', remediation, flags=re.IGNORECASE)
            remediation = re.sub(r'---PAGE \d+---', '', remediation)
            remediation = re.sub(r'\s*-\s*-\s*-', '', remediation)  # Remove separator lines
            
            # Clean up but preserve command structure
            lines = remediation.split('\n')
            cleaned_lines = []
            for line in lines:
                line = line.strip()
                if line:
                    # Preserve lines that look like commands (start with #, $, or common commands)
                    if re.match(r'^[#\$]|^(Run|Edit|Set|Add|Create|Modify|Remove|Ensure|Configure)', line, re.IGNORECASE):
                        cleaned_lines.append(line)
                    # Join other lines intelligently
                    elif cleaned_lines and not cleaned_lines[-1].rstrip().endswith(('.', '!', '?', ':', ';')):
                        cleaned_lines[-1] += ' ' + line
                    else:
                        cleaned_lines.append(line)
            
            remediation = '\n'.join(cleaned_lines)
            remediation = remediation.strip()
            
            return remediation if remediation else None
    
    return None

def update_milestone_file(milestone_path, cis_text):
    """Update a milestone file with complete description and remediation"""
    with open(milestone_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    updated_descriptions = 0
    updated_remediations = 0
    not_found = []
    
    for control in data.get('controls', []):
        control_id = control.get('id', '')
        if not control_id:
            continue
        
        # Find control section in document
        control_text = find_control_section(cis_text, control_id)
        
        if not control_text:
            not_found.append(control_id)
            continue
        
        # Extract description
        description = extract_description(control_text)
        if description:
            control['description'] = description
            updated_descriptions += 1
        
        # Extract remediation
        remediation = extract_remediation(control_text)
        if remediation:
            control['remediation'] = remediation
            updated_remediations += 1
        
        # Remove reference_note if we have actual content
        if (description or remediation) and 'reference_note' in control:
            del control['reference_note']
    
    # Write back updated file
    with open(milestone_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    return updated_descriptions, updated_remediations, not_found

def main():
    if len(sys.argv) < 4:
        print("Usage: python3 parse-ubuntu-cis-complete.py <cis_document> <milestones_dir> <ubuntu_version>")
        print("\nExample:")
        print("  python3 parse-ubuntu-cis-complete.py ~/Downloads/CIS_Ubuntu_22.04_Benchmark.pdf ubuntu-22.04/go-scanner/milestones 22.04")
        sys.exit(1)
    
    cis_doc_path = sys.argv[1]
    milestones_dir = sys.argv[2]
    ubuntu_version = sys.argv[3]
    
    if not os.path.exists(cis_doc_path):
        print(f"❌ CIS document not found: {cis_doc_path}")
        print(f"\n💡 Please provide the path to your official CIS Ubuntu {ubuntu_version} Benchmark document")
        print(f"   The document should be a PDF or RTF file.")
        sys.exit(1)
    
    if not os.path.exists(milestones_dir):
        print(f"❌ Milestones directory not found: {milestones_dir}")
        sys.exit(1)
    
    print("=" * 70)
    print("  Ubuntu CIS Benchmark Parser - Complete Description & Remediation")
    print("=" * 70)
    print(f"📄 CIS Document: {cis_doc_path}")
    print(f"📁 Milestones Directory: {milestones_dir}")
    print(f"🐧 Ubuntu Version: {ubuntu_version}")
    print()
    
    # Extract text from document
    print("🔄 Extracting text from document...")
    try:
        if cis_doc_path.lower().endswith('.pdf'):
            if not PDF_AVAILABLE:
                print("❌ PyPDF2 is required for PDF parsing.")
                print("   Install with: pip install PyPDF2")
                sys.exit(1)
            cis_text = extract_text_from_pdf(cis_doc_path)
        elif cis_doc_path.lower().endswith('.rtf'):
            cis_text = extract_text_from_rtf(cis_doc_path)
        else:
            print("❌ Unsupported file format. Please provide PDF or RTF file.")
            sys.exit(1)
    except Exception as e:
        print(f"❌ Error extracting text: {e}")
        sys.exit(1)
    
    print(f"✅ Extracted {len(cis_text):,} characters from document")
    print()
    
    # Find all milestone files
    milestone_files = sorted(Path(milestones_dir).glob('milestone-*.json'))
    
    if not milestone_files:
        print(f"❌ No milestone files found in {milestones_dir}")
        sys.exit(1)
    
    print(f"📋 Found {len(milestone_files)} milestone files")
    print("\n🔄 Parsing and updating milestone files...")
    print("   (This may take a few minutes for large documents)")
    print()
    
    total_descriptions = 0
    total_remediations = 0
    all_not_found = []
    
    for idx, milestone_file in enumerate(milestone_files, 1):
        descriptions, remediations, not_found = update_milestone_file(milestone_file, cis_text)
        total_descriptions += descriptions
        total_remediations += remediations
        all_not_found.extend(not_found)
        
        if descriptions > 0 or remediations > 0:
            print(f"  [{idx}/{len(milestone_files)}] ✓ {milestone_file.name}: {descriptions} descriptions, {remediations} remediations")
        if not_found:
            print(f"    ⚠️  Controls not found: {', '.join(not_found[:3])}")
            if len(not_found) > 3:
                print(f"    ... and {len(not_found) - 3} more")
    
    print()
    print("=" * 70)
    print("✅ PARSING COMPLETE")
    print("=" * 70)
    print(f"📊 Total descriptions added: {total_descriptions}")
    print(f"📊 Total remediations added: {total_remediations}")
    print(f"📊 Total fields updated: {total_descriptions + total_remediations}")
    
    if all_not_found:
        print(f"\n⚠️  {len(all_not_found)} controls not found in document")
        print("   These controls may have different IDs in the document.")
        print("   Sample missing IDs:", ', '.join(all_not_found[:10]))
    
    print(f"\n📝 All milestone files updated in: {milestones_dir}")
    print(f"✅ Ready to use with complete descriptions and remediation steps!")
    print()

if __name__ == '__main__':
    main()
