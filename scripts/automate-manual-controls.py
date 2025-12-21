#!/usr/bin/env python3
"""
Automate manual controls that can be automated.
Updates milestone files to convert manual controls to automated checks.
"""

import json
import os
import sys
from pathlib import Path

# Controls that can be automated with their automation config
AUTOMATION_MAP = {
    # File content checks - check if files exist and don't contain OS version info
    "1.6.1": {
        "type": "FileContent",
        "file_path": "/etc/motd",
        "pattern": "(Linux|Ubuntu|kernel|release|version|\\d+\\.\\d+)",
        "expected_result": "not_found",
        "automated": True
    },
    "1.6.2": {
        "type": "FileContent",
        "file_path": "/etc/issue",
        "pattern": "(Linux|Ubuntu|kernel|release|version|\\d+\\.\\d+)",
        "expected_result": "not_found",
        "automated": True
    },
    "1.6.3": {
        "type": "FileContent",
        "file_path": "/etc/issue.net",
        "pattern": "(Linux|Ubuntu|kernel|release|version|\\d+\\.\\d+)",
        "expected_result": "not_found",
        "automated": True
    },
    # Crontab access - check if cron.allow exists or cron.deny is configured
    "2.4.1.9": {
        "type": "FileContent",
        "file_path": "/etc/cron.allow /etc/cron.deny",
        "pattern": ".*",
        "expected_result": "found",
        "automated": True
    },
    # System accounts without valid login shell
    "5.4.2.7": {
        "type": "CommandOutputEmpty",
        "audit_command": "awk -F: '($1!~/^(root|halt|sync|shutdown)$/ && ($3<1000 || $3==65534) && $7!~/^(\\/usr\\/sbin\\/nologin|\\/sbin\\/nologin|\\/bin\\/false)$/) {print $1\":\"$3\":\"$7}' /etc/passwd",
        "automated": True
    },
    # Journald log file access - check Storage setting
    "6.1.1.2": {
        "type": "FileContent",
        "file_path": "/etc/systemd/journald.conf",
        "pattern": "Storage=(persistent|volatile|auto|none)",
        "expected_result": "found",
        "automated": True
    },
    # SUID/SGID files review - check for unexpected SUID/SGID files
    # Note: This will list all SUID/SGID files - manual review still needed for approval
    # But we can automate the detection
    "7.1.13": {
        "type": "CommandOutputEmpty",
        "audit_command": "df --local -P | awk '{if (NR!=1) print $6}' | xargs -I '{}' find '{}' -xdev -type f \\( -perm -4000 -o -perm -2000 \\) 2>/dev/null",
        "automated": True
    },
    # GDM controls - can be automated by checking dconf files
    "1.7.2": {
        "type": "FileContent",
        "file_path": "/etc/dconf/db/gdm.d/01-banner-message /etc/dconf/profile/gdm",
        "pattern": "banner-message-enable\\s*=\\s*true",
        "expected_result": "found",
        "automated": True
    },
    "1.7.3": {
        "type": "FileContent",
        "file_path": "/etc/dconf/db/gdm.d/00-login-screen",
        "pattern": "disable-user-list\\s*=\\s*true",
        "expected_result": "found",
        "automated": True
    },
    "1.7.4": {
        "type": "FileContent",
        "file_path": "/etc/dconf/db/local.d/00-screensaver",
        "pattern": "(idle-delay|lock-delay)",
        "expected_result": "found",
        "automated": True
    },
    "1.7.5": {
        "type": "FileContent",
        "file_path": "/etc/dconf/db/local.d/locks/00-screensaver",
        "pattern": "(idle-delay|lock-delay)",
        "expected_result": "found",
        "automated": True
    },
    "1.7.6": {
        "type": "FileContent",
        "file_path": "/etc/dconf/db/local.d/00-media-automount",
        "pattern": "automount\\s*=\\s*false",
        "expected_result": "found",
        "automated": True
    },
    "1.7.7": {
        "type": "FileContent",
        "file_path": "/etc/dconf/db/local.d/locks/00-media-automount",
        "pattern": "automount",
        "expected_result": "found",
        "automated": True
    },
    "1.7.8": {
        "type": "FileContent",
        "file_path": "/etc/dconf/db/local.d/00-media-autorun",
        "pattern": "autorun-never\\s*=\\s*true",
        "expected_result": "found",
        "automated": True
    },
    "1.7.9": {
        "type": "FileContent",
        "file_path": "/etc/dconf/db/local.d/locks/00-media-autorun",
        "pattern": "autorun-never",
        "expected_result": "found",
        "automated": True
    },
    "1.7.10": {
        "type": "FileContent",
        "file_path": "/etc/gdm3/custom.conf",
        "pattern": "Enable\\s*=\\s*false",
        "expected_result": "found",
        "automated": True
    },
    "1.7.11": {
        "type": "FileContent",
        "file_path": "/etc/gdm3/custom.conf",
        "pattern": "WaylandEnable\\s*=\\s*false",
        "expected_result": "found",
        "automated": True
    },
    # Firewall controls - can be automated by checking firewall rules
    "4.2.5": {
        "type": "CommandOutputEmpty",
        "audit_command": "ufw status numbered | grep -E '^\\[.*\\].*OUT.*ALLOW'",
        "automated": True
    },
    "4.3.3": {
        "type": "CommandOutputEmpty",
        "audit_command": "iptables -L -n | grep -v '^Chain' | grep -v '^target' | grep -v '^$' | grep -v '^\\s*$'",
        "automated": True
    },
    "4.3.7": {
        "type": "CommandOutputEmpty",
        "audit_command": "nft list ruleset | grep -E '(output|ct state established|ct state new)'",
        "automated": True
    },
    # iptables controls - can check if rules exist
    "4.4.2.1": {
        "type": "CommandOutputEmpty",
        "audit_command": "iptables -L | grep -E 'Chain (INPUT|OUTPUT|FORWARD).*policy (DROP|REJECT)'",
        "automated": True
    },
    "4.4.2.2": {
        "type": "CommandOutputEmpty",
        "audit_command": "iptables -L INPUT -v -n | grep -E 'lo.*ACCEPT'",
        "automated": True
    },
    "4.4.2.3": {
        "type": "CommandOutputEmpty",
        "audit_command": "iptables -L OUTPUT -v -n | grep -E '(ESTABLISHED|NEW).*ACCEPT'",
        "automated": True
    },
    "4.4.2.4": {
        "type": "CommandOutputEmpty",
        "audit_command": "ss -tuln | awk '{print $5}' | cut -d: -f2 | sort -u | while read port; do iptables -L INPUT -v -n | grep -q \":$port\" || echo \"Port $port not in iptables\"; done",
        "automated": True
    },
    # ip6tables controls
    "4.4.3.1": {
        "type": "CommandOutputEmpty",
        "audit_command": "ip6tables -L | grep -E 'Chain (INPUT|OUTPUT|FORWARD).*policy (DROP|REJECT)'",
        "automated": True
    },
    "4.4.3.2": {
        "type": "CommandOutputEmpty",
        "audit_command": "ip6tables -L INPUT -v -n | grep -E 'lo.*ACCEPT'",
        "automated": True
    },
    "4.4.3.3": {
        "type": "CommandOutputEmpty",
        "audit_command": "ip6tables -L OUTPUT -v -n | grep -E '(ESTABLISHED|NEW).*ACCEPT'",
        "automated": True
    },
    "4.4.3.4": {
        "type": "CommandOutputEmpty",
        "audit_command": "ss -tuln | awk '{print $5}' | grep '\\[.*\\]' | cut -d: -f2 | sort -u | while read port; do ip6tables -L INPUT -v -n | grep -q \":$port\" || echo \"Port $port not in ip6tables\"; done",
        "automated": True
    }
}

def update_milestone_file(milestone_path, automation_map):
    """Update milestone file to automate manual controls"""
    with open(milestone_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    updated_count = 0
    for control in data.get('controls', []):
        control_id = control.get('id', '')
        if control_id in automation_map:
            config = automation_map[control_id]
            
            # Update type and automated status
            old_type = control.get('type', 'Manual')
            control['type'] = config['type']
            control['automated'] = config['automated']
            
            # Add automation-specific fields
            if config['type'] == 'FileContent':
                control['file_path'] = config['file_path']
                control['pattern'] = config['pattern']
                control['expected_result'] = config['expected_result']
            elif config['type'] == 'CommandOutputEmpty':
                control['audit_command'] = config['audit_command']
            
            # Remove Manual type if present (already handled by type change)
            updated_count += 1
            print(f"  ✓ {control_id}: {old_type} → {config['type']}")
    
    if updated_count > 0:
        with open(milestone_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    return updated_count

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 automate-manual-controls.py <milestones_dir> [ubuntu_version]")
        print("\nExample:")
        print("  python3 automate-manual-controls.py ubuntu-24.04/milestones 24.04")
        sys.exit(1)
    
    milestones_dir = sys.argv[1]
    ubuntu_version = sys.argv[2] if len(sys.argv) > 2 else "24.04"
    
    if not os.path.exists(milestones_dir):
        print(f"❌ Milestones directory not found: {milestones_dir}")
        sys.exit(1)
    
    print("=" * 70)
    print("  Automate Manual Controls")
    print("=" * 70)
    print(f"📁 Milestones Directory: {milestones_dir}")
    print(f"🐧 Ubuntu Version: {ubuntu_version}")
    print(f"📋 Controls to automate: {len(AUTOMATION_MAP)}")
    print()
    
    # Find all milestone files
    milestone_files = sorted(Path(milestones_dir).glob('milestone-*.json'))
    
    if not milestone_files:
        print(f"❌ No milestone files found in {milestones_dir}")
        sys.exit(1)
    
    print(f"📋 Found {len(milestone_files)} milestone files")
    print("\n🔄 Automating manual controls...")
    print()
    
    total_updated = 0
    for milestone_file in milestone_files:
        updated = update_milestone_file(milestone_file, AUTOMATION_MAP)
        total_updated += updated
    
    print()
    print("=" * 70)
    print("✅ AUTOMATION COMPLETE")
    print("=" * 70)
    print(f"📊 Total controls automated: {total_updated}")
    print(f"📝 All milestone files updated in: {milestones_dir}")
    print()
    print("Controls automated:")
    for ctrl_id in AUTOMATION_MAP.keys():
        if total_updated > 0:
            print(f"  ✓ {ctrl_id}")
    print()

if __name__ == '__main__':
    main()

