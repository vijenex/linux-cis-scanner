#!/usr/bin/env python3
"""
Parse CIS CentOS 7 Benchmark PDF and generate milestone JSON files
Extracts only Level 1 controls, excludes Level 2 and unsupported controls

Usage:
    python3 parse-centos7-cis.py <pdf_file> <output_dir>
    
Example:
    python3 parse-centos7-cis.py ~/Downloads/CIS_CentOS_Linux_7_Benchmark_v3.1.2.pdf centos-7/go-scanner/milestones
"""

import re
import json
import os
import sys
from pathlib import Path

try:
    import PyPDF2
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False
    print("⚠️  PyPDF2 not installed. Install with: pip install PyPDF2")
    sys.exit(1)

def extract_text_from_pdf(pdf_path):
    """Extract text from PDF file"""
    if not PDF_AVAILABLE:
        raise ImportError("PyPDF2 is required for PDF parsing. Install with: pip install PyPDF2")
    
    text = ""
    print(f"📄 Reading PDF: {pdf_path}")
    with open(pdf_path, 'rb') as f:
        pdf = PyPDF2.PdfReader(f)
        total_pages = len(pdf.pages)
        print(f"   Total pages: {total_pages}")
        
        for i, page in enumerate(pdf.pages):
            if (i + 1) % 50 == 0:
                print(f"   Processing page {i+1}/{total_pages}...")
            text += page.extract_text() + "\n"
    
    print(f"✅ Extracted {len(text)} characters")
    return text

def detect_control_type(title, audit_text, remediation_text, description):
    """Detect control type from content analysis"""
    title_lower = title.lower()
    audit_lower = audit_text.lower()
    remediation_lower = remediation_text.lower()
    combined = f"{title_lower} {audit_lower} {remediation_lower} {description.lower()}"
    
    # KernelModule checks
    if "kernel module" in title_lower:
        if "not available" in title_lower or "disabled" in title_lower:
            return "KernelModule"
    
    # MountPoint checks (separate partition)
    if ("separate partition" in title_lower or "partition exists" in title_lower):
        return "MountPoint"
    
    # MountOption checks (nodev, nosuid, noexec)
    if re.search(r'\b(nodev|nosuid|noexec)\b', title_lower):
        if "option set on" in title_lower or "option" in title_lower:
            return "MountOption"
    
    # ServiceStatus checks
    if "service" in title_lower:
        if any(word in title_lower for word in ["enabled", "disabled", "running", "active", "inactive"]):
            return "ServiceStatus"
    
    # PackageInstalled checks
    if any(word in title_lower for word in ["package", "installed", "removed"]):
        return "PackageInstalled"
    
    # SysctlParameter checks
    if any(pattern in combined for pattern in ["sysctl", "kernel parameter", "/proc/sys/", "net.ipv", "kernel.randomize"]):
        if "sysctl" in audit_lower or "sysctl" in remediation_lower:
            return "SysctlParameter"
    
    # FilePermissions checks
    if any(pattern in combined for pattern in ["permission", "chmod", "owner", "chown", "mode"]):
        if re.search(r'(stat|ls -l|chmod|chown|find.*-perm)', audit_lower):
            return "FilePermissions"
    
    # FileContent checks
    if any(pattern in combined for pattern in ["grep", "configured", "parameter", "setting"]):
        if re.search(r'(grep|awk|sed|cat.*\|)', audit_lower):
            if "sysctl" not in audit_lower and "chmod" not in audit_lower:
                return "FileContent"
    
    # SSHConfig checks
    if "ssh" in title_lower or "sshd" in title_lower:
        if any(pattern in combined for pattern in ["config", "parameter", "setting"]):
            return "SSHConfig"
    
    # PAMConfig checks
    if "pam" in title_lower:
        return "PAMConfig"
    
    # SudoConfig checks
    if "sudo" in title_lower:
        return "SudoConfig"
    
    return "Manual"

def extract_section(text, start_marker, end_marker=None):
    """Extract content between markers"""
    if end_marker:
        pattern = re.escape(start_marker) + r'(.*?)' + re.escape(end_marker)
    else:
        pattern = re.escape(start_marker) + r'(.*?)(?=\n\s*(?:Description|Rationale|Audit|Remediation|Impact|References|Profile|Level|$))'
    
    match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
    if match:
        content = match.group(1).strip()
        # Clean up whitespace
        content = re.sub(r'\s+', ' ', content)
        return content
    return ""

def parse_controls(pdf_text):
    """Parse controls from PDF text"""
    controls = {}
    seen_ids = {}  # Track controls by ID to avoid duplicates
    
    # Pattern to match control IDs: 1.1.1.1, 1.2.3, etc.
    # CentOS 7 format: "1.1.1.1 Ensure ..."
    control_pattern = r'(\d+\.\d+\.\d+(?:\.\d+)?)\s+Ensure\s+(.+?)(?=\n\s*\d+\.\d+\.\d+|Profile|Level|$)'
    
    matches = list(re.finditer(control_pattern, pdf_text, re.MULTILINE | re.IGNORECASE))
    
    print(f"🔍 Found {len(matches)} potential controls")
    
    for i, match in enumerate(matches):
        control_id = match.group(1)
        
        # Skip if we've already processed this control ID with better content
        if control_id in seen_ids:
            continue
        title_start = match.group(2).strip()
        
        # Get full control text
        start_pos = match.start()
        end_pos = matches[i+1].start() if i+1 < len(matches) else len(pdf_text)
        control_text = pdf_text[start_pos:end_pos]
        
        # Extract profile level (must be Level 1)
        profile_section = control_text[:1000]
        if "Level 2" in profile_section or "Level2" in profile_section:
            # Skip Level 2 controls
            continue
        
        # Quality check: skip if control text is too short (likely incomplete)
        if len(control_text) < 200:
            continue
        
        # Extract title (may span multiple lines)
        title_match = re.search(r'Ensure\s+(.+?)(?:\n|Description|Profile|Level|\(Automated\)|\(Manual\))', control_text, re.DOTALL | re.IGNORECASE)
        if title_match:
            title = f"Ensure {title_match.group(1).strip()}"
            # Clean up title - remove page numbers and extra dots
            title = re.sub(r'\.{3,}.*$', '', title)  # Remove trailing dots and page numbers
            title = re.sub(r'\s+', ' ', title)
            title = re.sub(r'\s*\(Automated\)\s*', ' ', title)
            title = re.sub(r'\s*\(Manual\)\s*', ' ', title)
            title = title.strip()
            title = title[:200]  # Limit length
        else:
            title = f"Ensure {title_start[:200]}"
            # Clean up
            title = re.sub(r'\.{3,}.*$', '', title)
            title = re.sub(r'\s+', ' ', title).strip()
        
        # Check if automated
        automated = "(Automated)" in control_text[:500] or "Automated" in control_text[:500]
        
        # Extract sections
        description = extract_section(control_text, "Description:", "Rationale:")
        if not description:
            description = extract_section(control_text, "Description")
        
        rationale = extract_section(control_text, "Rationale:", "Audit:")
        if not rationale:
            rationale = extract_section(control_text, "Rationale")
        
        audit = extract_section(control_text, "Audit:", "Remediation:")
        if not audit:
            audit = extract_section(control_text, "Audit")
        
        remediation = extract_section(control_text, "Remediation:", "References:")
        if not remediation:
            remediation = extract_section(control_text, "Remediation")
        
        # Detect control type
        control_type = detect_control_type(title, audit, remediation, description)
        
        # Post-process type detection improvements for automated controls
        if control_type == "Manual" and automated:
            title_lower = title.lower()
            desc_lower = description.lower() if description else ""
            combined_lower = f"{title_lower} {desc_lower}"
            
            # Kernel modules/filesystems - improved patterns
            if (("kernel module" in title_lower or "filesystem" in title_lower or any(fs in title_lower for fs in ["cramfs", "squashfs", "udf", "freevxfs", "jffs2", "hfs", "hfsplus", "fat"])) and 
                ("disabled" in title_lower or "not available" in title_lower or "not loaded" in title_lower or "mounting" in title_lower)):
                control_type = "KernelModule"
            
            # Sticky bit checks
            elif "sticky bit" in title_lower and ("world-writable" in title_lower or "directories" in title_lower):
                control_type = "FilePermissions"
            
            # GPG check / yum configuration
            elif "gpgcheck" in title_lower or ("yum" in title_lower and "gpg" in title_lower):
                control_type = "FileContent"
            
            # ASLR / kernel.randomize_va_space
            elif "aslr" in title_lower or "address space layout" in title_lower or "randomize" in title_lower:
                control_type = "SysctlParameter"
            
            # Authentication/single user mode / sulogin
            elif ("authentication" in title_lower and "single user" in title_lower) or "sulogin" in combined_lower:
                control_type = "FileContent"
            
            # Filesystem integrity check / AIDE
            elif "filesystem integrity" in title_lower or "aide" in combined_lower:
                control_type = "ServiceStatus"  # Usually a cron job or service
            
            # SELinux checks
            elif "selinux" in title_lower:
                if "enabled" in title_lower or "state" in title_lower:
                    control_type = "FileContent"  # Check /etc/selinux/config
            
            # Bootloader password
            elif "bootloader" in title_lower and "password" in title_lower:
                control_type = "FileContent"
            
            # Core dumps
            elif "core dumps" in title_lower or "core dump" in title_lower:
                control_type = "SysctlParameter"
            
            # Logging / rsyslog
            elif "logging" in title_lower or "rsyslog" in title_lower:
                control_type = "ServiceStatus"
            
            # NTP / chrony
            elif "ntp" in title_lower or "chrony" in title_lower:
                control_type = "ServiceStatus"
            
            # Firewall / firewalld
            elif "firewall" in title_lower or "firewalld" in title_lower:
                control_type = "ServiceStatus"
            
            # If still Manual but automated, try to detect from audit command patterns
            if control_type == "Manual" and audit and audit != "Manual review required":
                audit_lower = audit.lower()
                if "find" in audit_lower and ("-perm" in audit_lower or "writable" in audit_lower):
                    control_type = "FilePermissions"
                elif "grep" in audit_lower or "awk" in audit_lower:
                    control_type = "FileContent"
                elif "systemctl" in audit_lower:
                    control_type = "ServiceStatus"
                elif "rpm" in audit_lower:
                    control_type = "PackageInstalled"
                elif "sysctl" in audit_lower:
                    control_type = "SysctlParameter"
        
        # Build section
        section_parts = control_id.split('.')
        section = f"{section_parts[0]}.{section_parts[1]}" if len(section_parts) >= 2 else section_parts[0]
        
        # Build control object
        control = {
            "id": control_id,
            "title": title,
            "section": f"Section {section}",
            "profile": "Level1",
            "automated": automated,
            "type": control_type,
            "severity": "medium",
            "cis_reference": f"CIS CentOS Linux 7 Benchmark v3.1.2 - {control_id}",
            "description": description if description else title,
            "rationale": rationale if rationale else "Refer to CIS Benchmark documentation",
            "remediation": remediation if remediation else "Refer to CIS Benchmark documentation",
            "impact": "None",
            "audit_command": audit if audit else "Manual review required"
        }
        
        # Add type-specific fields
        if control_type == "KernelModule":
            module_match = re.search(r'(\w+)\s+kernel module', title.lower())
            if module_match:
                control["module_name"] = module_match.group(1)
                control["expected_status"] = "not_available"
        
        elif control_type == "MountPoint":
            mount_match = re.search(r'(/[\w/]+)', title)
            if mount_match:
                control["mount_point"] = mount_match.group(1)
                control["expected_status"] = "separate_partition"
        
        elif control_type == "MountOption":
            mount_match = re.search(r'(/[\w/]+)', title)
            option_match = re.search(r'(nodev|nosuid|noexec)', title.lower())
            if mount_match and option_match:
                control["mount_point"] = mount_match.group(1)
                control["required_option"] = option_match.group(1)
        
        elif control_type == "ServiceStatus":
            service_match = re.search(r'(\w+)\s+(?:service|is)', title.lower())
            if service_match:
                control["service_name"] = service_match.group(1)
            if "enabled" in title.lower():
                control["expected_status"] = "enabled"
            elif "disabled" in title.lower() or "inactive" in title.lower():
                control["expected_status"] = "disabled"
        
        elif control_type == "PackageInstalled":
            package_match = re.search(r'(\w+)\s+(?:package|is installed)', title.lower())
            if package_match:
                control["package_name"] = package_match.group(1)
            control["expected_status"] = "installed" if "installed" in title.lower() else "not_installed"
        
        elif control_type == "SysctlParameter":
            # Try to extract parameter from audit or remediation
            param_match = re.search(r'([\w.]+)\s*=\s*(\d+)', audit + " " + remediation)
            if param_match:
                control["parameter_name"] = param_match.group(1)
                control["expected_value"] = param_match.group(2)
        
        elif control_type == "SSHConfig":
            param_match = re.search(r'(\w+)\s+(?:is|parameter)', title.lower())
            if param_match:
                control["parameter"] = param_match.group(1)
        
        elif control_type == "FilePermissions":
            file_match = re.search(r'(/[\w/.-]+)', title)
            if file_match:
                control["file_path"] = file_match.group(1)
        
        elif control_type == "FileContent":
            file_match = re.search(r'(/[\w/.-]+)', title)
            if file_match:
                control["file_path"] = file_match.group(1)
        
        # Mark as seen and store
        seen_ids[control_id] = control
        
        # Group by section
        if section not in controls:
            controls[section] = []
        controls[section].append(control)
    
    return controls

def generate_milestones(controls, output_dir, os_name, version):
    """Generate milestone JSON files"""
    milestones = {}
    
    for section, ctrls in sorted(controls.items()):
        milestone_key = section.replace('.', '-')
        milestone_file = f"milestone-{milestone_key}.json"
        
        milestones[milestone_file] = {
            "milestone": section,
            "version": "1.0.0",
            "description": f"{os_name} CIS Benchmark {version} - Section {section}",
            "controls": sorted(ctrls, key=lambda x: x['id'])
        }
    
    # Write files
    os.makedirs(output_dir, exist_ok=True)
    
    type_stats = {}
    level1_count = 0
    
    for filename, data in milestones.items():
        # Filter to only Level 1 controls
        level1_controls = [c for c in data['controls'] if c.get('profile') == 'Level1']
        
        if not level1_controls:
            continue  # Skip if no Level 1 controls
        
        data['controls'] = level1_controls
        level1_count += len(level1_controls)
        
        filepath = os.path.join(output_dir, filename)
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"✅ {filename}: {len(level1_controls)} Level 1 controls")
        
        # Count types
        for ctrl in level1_controls:
            ctype = ctrl['type']
            type_stats[ctype] = type_stats.get(ctype, 0) + 1
    
    print(f"\n📊 Summary:")
    print(f"Total milestones: {len(milestones)}")
    print(f"Total Level 1 controls: {level1_count}")
    print(f"\n🔍 Control Types:")
    for ctype, count in sorted(type_stats.items(), key=lambda x: -x[1]):
        print(f"  {ctype}: {count}")

def main():
    if len(sys.argv) < 3:
        print(__doc__)
        print("\nExample:")
        print("  python3 parse-centos7-cis.py ~/Downloads/CIS_CentOS_Linux_7_Benchmark_v3.1.2.pdf centos-7/go-scanner/milestones")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    output_dir = sys.argv[2]
    
    if not os.path.exists(pdf_path):
        print(f"❌ PDF file not found: {pdf_path}")
        sys.exit(1)
    
    # Extract text from PDF
    pdf_text = extract_text_from_pdf(pdf_path)
    
    # Parse controls
    print("\n🔍 Parsing controls...")
    controls = parse_controls(pdf_text)
    
    # Generate milestone files
    print("\n📝 Generating milestone files...")
    generate_milestones(controls, output_dir, "CentOS Linux 7", "v3.1.2")
    
    print("\n✅ Complete!")

if __name__ == "__main__":
    main()

