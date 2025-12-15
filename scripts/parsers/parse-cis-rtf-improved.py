#!/usr/bin/env python3
"""
Improved CIS Benchmark RTF Parser
Extracts audit commands, remediation, and properly detects control types from RTF content.

Usage:
    python3 parse-cis-rtf-improved.py <rtf_file> <output_dir> <os_name> <version>
"""

import re
import json
import os
import sys

def clean_rtf_text(text):
    """Remove RTF formatting and clean text"""
    # Remove RTF control words
    text = re.sub(r'\\[a-z]+\d*\s?', ' ', text)
    # Remove braces
    text = re.sub(r'[{}]', '', text)
    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text)
    # Remove escape sequences
    text = re.sub(r'\\\\.', '', text)
    return text.strip()

def extract_section_content(content, start_marker, end_marker=None):
    """Extract content between markers"""
    pattern = re.escape(start_marker) + r'(.*?)' + (re.escape(end_marker) if end_marker else r'(?=\\f[13]\\b|$)')
    match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)
    if match:
        return clean_rtf_text(match.group(1))
    return ""

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
            # Exclude sysctl and permission checks
            if "sysctl" not in audit_lower and "chmod" not in audit_lower:
                return "FileContent"
    
    return "Manual"

def extract_audit_command(raw_audit_section):
    """Extract actual shell commands from audit section"""
    # Look for shell script blocks (#!/usr/bin/env bash or #!/bin/bash)
    script_match = re.search(r'#!/(?:usr/bin/env bash|bin/bash)(.*?)(?=\\f[12]\\b|Remediation:|References:|$)', 
                            raw_audit_section, re.DOTALL)
    if script_match:
        script = clean_rtf_text(script_match.group(1))
        # Extract key commands (simplified)
        lines = [l.strip() for l in script.split('\\n') if l.strip() and not l.strip().startswith('#')]
        if lines:
            return ' '.join(lines[:3])  # First 3 meaningful lines
    
    # Fallback: look for common command patterns
    commands = []
    for pattern in [r'(lsmod.*?grep)', r'(modprobe.*?showconfig)', r'(findmnt.*?)', 
                   r'(systemctl.*?)', r'(rpm -q.*?)', r'(sysctl.*?)', r'(stat.*?)', r'(grep.*?)']:
        match = re.search(pattern, raw_audit_section, re.IGNORECASE)
        if match:
            commands.append(clean_rtf_text(match.group(1)))
    
    return '; '.join(commands) if commands else "Manual review required"

def extract_remediation_steps(raw_remediation_section):
    """Extract remediation commands"""
    # Look for shell script blocks
    script_match = re.search(r'#!/(?:usr/bin/env bash|bin/bash)(.*?)(?=\\f[12]\\b|References:|CIS Controls:|$)', 
                            raw_remediation_section, re.DOTALL)
    if script_match:
        return clean_rtf_text(script_match.group(1))[:500]  # Limit length
    
    # Fallback: extract bullet points or commands
    cleaned = clean_rtf_text(raw_remediation_section)
    return cleaned[:500] if cleaned else "Refer to CIS Benchmark documentation"

def parse_rtf(rtf_path, output_dir, os_name, version):
    """Parse RTF and generate milestone JSON files"""
    with open(rtf_path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    
    # Find all control sections
    control_pattern = r'(\\d+\\.\\d+\\.\\d+(?:\\.\\d+)*)\\s+Ensure\\s+([^(]+)\\(([^)]+)\\)'
    controls = {}
    
    matches = list(re.finditer(control_pattern, content))
    
    for i, match in enumerate(matches):
        control_id = match.group(1)
        title = match.group(2).strip()
        automation = match.group(3).strip()
        
        # Extract section between this control and next
        start_pos = match.start()
        end_pos = matches[i+1].start() if i+1 < len(matches) else len(content)
        control_content = content[start_pos:end_pos]
        
        # Extract sections
        profile_section = control_content[:500]
        profile = "Level2" if "Level 2" in profile_section else "Level1"
        
        description = extract_section_content(control_content, "Description:", "Rationale:")
        rationale = extract_section_content(control_content, "Rationale:", "Audit:")
        
        # Extract audit section (raw for command extraction)
        audit_match = re.search(r'Audit:(.*?)(?=Remediation:|Impact:|References:|$)', control_content, re.DOTALL | re.IGNORECASE)
        raw_audit = audit_match.group(1) if audit_match else ""
        audit_command = extract_audit_command(raw_audit)
        
        # Extract remediation section
        remediation_match = re.search(r'Remediation:(.*?)(?=References:|Impact:|CIS Controls:|$)', control_content, re.DOTALL | re.IGNORECASE)
        raw_remediation = remediation_match.group(1) if remediation_match else ""
        remediation = extract_remediation_steps(raw_remediation)
        
        impact = extract_section_content(control_content, "Impact:", "Audit:")
        if not impact:
            impact = "None"
        
        # Detect control type
        control_type = detect_control_type(title, raw_audit, raw_remediation, description)
        
        # Build control object
        section_parts = control_id.split('.')
        section = f"{section_parts[0]}.{section_parts[1]}" if len(section_parts) >= 2 else section_parts[0]
        
        control = {
            "id": control_id,
            "title": f"Ensure {title}",
            "section": f"Section {section}",
            "profile": profile,
            "automated": automation.lower() == "automated",
            "type": control_type,
            "severity": "medium",
            "cis_reference": f"CIS {os_name} {version} - {control_id}",
            "description": description if description else f"Ensure {title}",
            "rationale": rationale if rationale else "Refer to CIS Benchmark documentation",
            "remediation": remediation,
            "impact": impact,
            "audit_command": audit_command
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
            param_match = re.search(r'([\w.]+)\s*=\s*(\d+)', audit_command)
            if param_match:
                control["parameter_name"] = param_match.group(1)
                control["expected_value"] = param_match.group(2)
        
        # Group by section
        if section not in controls:
            controls[section] = []
        controls[section].append(control)
    
    # Generate milestone files
    milestones = {}
    for section, ctrls in sorted(controls.items()):
        milestone_key = section.replace('.', '-')
        milestone_file = f"milestone-{milestone_key}.json"
        
        if milestone_file not in milestones:
            milestones[milestone_file] = {
                "milestone": section,
                "version": "1.0.0",
                "description": f"{os_name} CIS Benchmark {version} - Section {section}",
                "controls": []
            }
        
        milestones[milestone_file]["controls"].extend(ctrls)
    
    # Write files
    os.makedirs(output_dir, exist_ok=True)
    
    type_stats = {}
    for filename, data in milestones.items():
        filepath = os.path.join(output_dir, filename)
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"✅ {filename}: {len(data['controls'])} controls")
        
        # Count types
        for ctrl in data['controls']:
            ctype = ctrl['type']
            type_stats[ctype] = type_stats.get(ctype, 0) + 1
    
    print(f"\n📊 Summary:")
    print(f"Total milestones: {len(milestones)}")
    print(f"Total controls: {sum(len(m['controls']) for m in milestones.values())}")
    print(f"\n🔍 Control Types:")
    for ctype, count in sorted(type_stats.items(), key=lambda x: -x[1]):
        print(f"  {ctype}: {count}")

if __name__ == "__main__":
    if len(sys.argv) != 5:
        print(__doc__)
        sys.exit(1)
    
    parse_rtf(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])
