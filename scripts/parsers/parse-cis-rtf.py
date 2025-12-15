#!/usr/bin/env python3
"""
CIS Benchmark RTF Parser - IMPROVED
Parses CIS benchmark RTF files with better control type detection.

Usage:
    python3 parse-cis-rtf.py <rtf_file> <output_dir> <os_name> <version>
"""

import re
import json
import os
import sys

# Service name mapping
SERVICE_MAP = {
    "dhcp server": "dhcpd", "dns server": "named", "ftp server": "vsftpd",
    "web server": "httpd", "mail transfer agent": "postfix", "print server": "cups",
    "rpcbind": "rpcbind", "rsync": "rsync", "snmp": "snmpd",
    "telnet server": "telnet.socket", "tftp server": "tftp.socket",
    "xinetd": "xinetd", "avahi": "avahi-daemon", "samba": "smb",
    "dnsmasq": "dnsmasq", "nis server": "ypserv", "nfs": "nfs-server",
    "message access": "dovecot", "web proxy": "squid", "autofs": "autofs",
    "bluetooth": "bluetooth", "cron": "crond", "chrony": "chronyd",
}

PACKAGE_MAP = {
    "x window": "xorg-x11-server-common", "telnet client": "telnet",
    "ftp client": "ftp", "nis client": "ypbind", "tftp client": "tftp",
    "ldap client": "openldap-clients", "aide": "aide", "selinux": "libselinux",
    "setroubleshoot": "setroubleshoot", "gdm": "gdm", "nftables": "nftables",
    "sudo": "sudo", "pam": "pam", "authselect": "authselect",
    "libpwquality": "libpwquality", "rsyslog": "rsyslog",
    "systemd-journal-remote": "systemd-journal-remote", "chrony": "chrony",
}

def detect_control_type(title, content_window):
    """Detect control type from title and surrounding content"""
    text = f"{title} {content_window}".lower()
    
    # MountOption - CHECK FIRST
    if re.search(r'\b(nodev|nosuid|noexec)\b', title.lower()) and 'option' in title.lower():
        return "MountOption"
    
    # KernelModule
    if re.search(r'\b(lsmod|modprobe|blacklist|kernel module)', text):
        return "KernelModule"
    
    # SysctlParameter
    if re.search(r'\b(sysctl|/proc/sys|kernel\.|net\.)', text):
        return "SysctlParameter"
    
    # MountPoint
    if re.search(r'\b(separate partition|partition exists)', text):
        return "MountPoint"
    
    # ServiceStatus
    if re.search(r'\b(systemctl|service.*enabled|service.*disabled|services are not in use)', text):
        return "ServiceStatus"
    
    # PackageInstalled
    if re.search(r'\b(rpm -q|package.*installed|client is not installed|is installed)', text):
        return "PackageInstalled"
    
    # FilePermissions
    if re.search(r'\b(chmod|chown|permission|stat -c)', text):
        return "FilePermissions"
    
    # FileContent
    if re.search(r'\b(grep|/etc/.*\.conf)', text) and 'sysctl' not in text:
        return "FileContent"
    
    return "Manual"

def extract_fields(control_type, title, content_window):
    """Extract required fields based on control type"""
    fields = {}
    title_lower = title.lower()
    
    if control_type == "ServiceStatus":
        # Extract service name
        for key, service in SERVICE_MAP.items():
            if key in title_lower:
                fields["service_name"] = service
                break
        fields["expected_status"] = "disabled" if "not in use" in title_lower else "enabled"
    
    elif control_type == "PackageInstalled":
        # Extract package name
        for key, pkg in PACKAGE_MAP.items():
            if key in title_lower:
                fields["package_name"] = pkg
                break
        fields["expected_status"] = "not_installed" if "not installed" in title_lower else "installed"
    
    elif control_type == "SysctlParameter":
        # Extract parameter from title or content
        param_match = re.search(r'([a-z0-9_.]+)\s+is\s+(set|disabled|enabled)', title_lower)
        if param_match:
            fields["parameter_name"] = param_match.group(1)
            fields["expected_value"] = "1" if "enabled" in title_lower else "0"
    
    elif control_type == "FilePermissions":
        # Extract file path
        path_match = re.search(r'(/etc/[a-zA-Z0-9_./-]+)', title)
        if path_match:
            fields["file_path"] = path_match.group(1)
            fields["expected_permissions"] = "0644"
            fields["expected_owner"] = "root"
            fields["expected_group"] = "root"
    
    elif control_type == "FileContent":
        # Extract file path
        path_match = re.search(r'(/etc/[a-zA-Z0-9_./-]+)', title)
        if path_match:
            fields["file_path"] = path_match.group(1)
            fields["pattern"] = ".*"
            fields["expected_result"] = "found"
    
    return fields

def parse_rtf(rtf_path, output_dir, os_name, version):
    with open(rtf_path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()

    # Remove RTF formatting
    content = re.sub(r'\\[a-z]+\d*\s?', ' ', content)
    content = re.sub(r'[{}]', '', content)
    content = re.sub(r'\s+', ' ', content)

    # Extract controls
    controls = {}
    pattern = r'(\d+\.\d+\.\d+(?:\.\d+)*)\s+Ensure\s+([^(]+)\(([^)]+)\)'

    matches = list(re.finditer(pattern, content))
    for i, match in enumerate(matches):
        control_id = match.group(1)
        title = match.group(2).strip()
        automation = match.group(3).strip()
        
        # Get content window for type detection
        start = match.start()
        end = matches[i+1].start() if i+1 < len(matches) else start + 2000
        content_window = content[start:end]
        
        # Determine section
        section_parts = control_id.split('.')
        section = f"{section_parts[0]}.{section_parts[1]}" if len(section_parts) >= 2 else section_parts[0]
        
        # Profile detection
        profile = "Level2" if "Level 2" in content_window[:500] else "Level1"
        
        # Detect control type
        control_type = detect_control_type(title, content_window)
        
        # Extract required fields
        extracted_fields = extract_fields(control_type, title, content_window)
        
        control = {
            "id": control_id,
            "title": f"Ensure {title}",
            "section": f"Section {section}",
            "profile": profile,
            "automated": automation.lower() == "automated",
            "type": control_type,
            "severity": "medium",
            "cis_reference": f"CIS {os_name} {version} - {control_id}",
            "description": f"Ensure {title}",
            "rationale": "Refer to CIS Benchmark documentation",
            "remediation": "Refer to CIS Benchmark documentation",
            "impact": "None",
            "audit_command": "Manual review required"
        }
        
        # Add extracted fields
        control.update(extracted_fields)
        
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
        
        if section not in controls:
            controls[section] = []
        controls[section].append(control)

    # Group by milestone
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

    # Write milestone files
    os.makedirs(output_dir, exist_ok=True)
    type_stats = {}
    
    for filename, data in milestones.items():
        filepath = os.path.join(output_dir, filename)
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"✅ {filename}: {len(data['controls'])} controls")
        
        for ctrl in data['controls']:
            ctype = ctrl['type']
            type_stats[ctype] = type_stats.get(ctype, 0) + 1

    print(f"\n📊 Summary:")
    print(f"Total milestones: {len(milestones)}")
    print(f"Total controls: {sum(len(m['controls']) for m in milestones.values())})")
    print(f"\n🔍 Control Types:")
    for ctype, count in sorted(type_stats.items(), key=lambda x: -x[1]):
        print(f"  {ctype}: {count}")

if __name__ == "__main__":
    if len(sys.argv) != 5:
        print(__doc__)
        sys.exit(1)
    
    parse_rtf(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])
