#!/usr/bin/env python3
"""
Fix missing fields in milestone JSON files.
Adds service_name, package_name, file_path, module_name, etc. based on control type and audit commands.
"""

import json
import glob
import re
import os

# Manual mappings for controls where auto-detection fails
MANUAL_MAPPINGS = {
    # Section 1.3 - AIDE and Secure Boot
    '1.3.1.1': {'package_name': 'aide'},
    '1.3.1.2': {'file_path': '/etc/cron.d/aide', 'pattern': 'aide', 'expected_result': 'present'},
    '1.3.1.7': {'package_name': 'grub2-efi-x64'},
    '1.3.1.8': {'package_name': 'shim-x64'},
    
    # Section 1.4 - Bootloader
    '1.4.1': {'file_path': '/boot/grub2/grub.cfg', 'expected_permissions': '0600', 'expected_owner': 'root', 'expected_group': 'root'},
    '1.4.2': {'file_path': '/boot/grub2/user.cfg', 'expected_permissions': '0600', 'expected_owner': 'root', 'expected_group': 'root'},
    
    # Section 1.5 - Additional Process Hardening
    '1.5.9': {'file_path': '/etc/security/limits.conf', 'pattern': 'hard.*core.*0', 'expected_result': 'present'},
    '1.5.10': {'file_path': '/etc/sysctl.conf', 'pattern': 'fs.suid_dumpable.*=.*0', 'expected_result': 'present'},
    
    # Section 2.1 - Time Synchronization and Services
    '2.1.1': {'service_name': 'autofs', 'expected_status': 'inactive'},
    '2.1.2': {'service_name': 'avahi-daemon', 'expected_status': 'inactive'},
    '2.1.3': {'service_name': 'cockpit', 'expected_status': 'inactive'},
    '2.1.4': {'service_name': 'dhcpd', 'expected_status': 'inactive'},
    '2.1.5': {'service_name': 'named', 'expected_status': 'inactive'},
    '2.1.6': {'service_name': 'dnsmasq', 'expected_status': 'inactive'},
    '2.1.7': {'service_name': 'dovecot', 'expected_status': 'inactive'},
    '2.1.8': {'package_name': 'ftp'},
    '2.1.9': {'service_name': 'httpd', 'expected_status': 'inactive'},
    '2.1.10': {'service_name': 'nginx', 'expected_status': 'inactive'},
    '2.1.11': {'service_name': 'nfs-server', 'expected_status': 'inactive'},
    '2.1.12': {'service_name': 'rpcbind', 'expected_status': 'inactive'},
    '2.1.13': {'service_name': 'rsync', 'expected_status': 'inactive'},
    '2.1.14': {'service_name': 'smb', 'expected_status': 'inactive'},
    '2.1.15': {'service_name': 'snmpd', 'expected_status': 'inactive'},
    '2.1.16': {'service_name': 'squid', 'expected_status': 'inactive'},
    '2.1.17': {'service_name': 'tftp', 'expected_status': 'inactive'},
    '2.1.18': {'file_path': '/etc/xinetd.conf', 'pattern': 'xinetd', 'expected_result': 'absent'},
    '2.1.19': {'package_name': 'xorg-x11-server-common'},
    '2.1.20': {'service_name': 'ypserv', 'expected_status': 'inactive'},
    '2.1.21': {'file_path': '/etc/cups/cupsd.conf', 'pattern': 'Listen', 'expected_result': 'present'},
    '2.1.22': {'package_name': 'cups'},
    
    # Section 2.3 - Client Services
    '2.3.1': {'package_name': 'ypbind'},
    
    # Section 2.4 - Cron
    '2.4.1.1': {'file_path': '/etc/cron.d', 'expected_permissions': '0700', 'expected_owner': 'root', 'expected_group': 'root'},
    '2.4.1.2': {'file_path': '/etc/cron.daily', 'expected_permissions': '0700', 'expected_owner': 'root', 'expected_group': 'root'},
    '2.4.1.3': {'file_path': '/etc/cron.hourly', 'expected_permissions': '0700', 'expected_owner': 'root', 'expected_group': 'root'},
    '2.4.1.4': {'file_path': '/etc/cron.monthly', 'expected_permissions': '0700', 'expected_owner': 'root', 'expected_group': 'root'},
    '2.4.1.5': {'file_path': '/etc/cron.weekly', 'expected_permissions': '0700', 'expected_owner': 'root', 'expected_group': 'root'},
    '2.4.1.6': {'file_path': '/etc/crontab', 'expected_permissions': '0600', 'expected_owner': 'root', 'expected_group': 'root'},
    '2.4.1.7': {'file_path': '/etc/cron.allow', 'expected_permissions': '0600', 'expected_owner': 'root', 'expected_group': 'root'},
    '2.4.1.8': {'file_path': '/etc/cron.deny', 'expected_permissions': '0600', 'expected_owner': 'root', 'expected_group': 'root'},
    
    # Section 3 - Network Configuration
    '3.1.2': {'file_path': '/etc/sysconfig/network-scripts', 'pattern': 'BOOTPROTO=none', 'expected_result': 'present'},
    '3.1.3': {'service_name': 'bluetooth', 'expected_status': 'inactive'},
    '3.2.1': {'module_name': 'dccp', 'expected_status': 'blacklisted'},
    '3.2.2': {'module_name': 'sctp', 'expected_status': 'blacklisted'},
    '3.2.3': {'module_name': 'rds', 'expected_status': 'blacklisted'},
    '3.2.4': {'module_name': 'tipc', 'expected_status': 'blacklisted'},
    '3.2.5': {'module_name': 'bluetooth', 'expected_status': 'blacklisted'},
    '3.2.6': {'module_name': 'usb-storage', 'expected_status': 'blacklisted'},
    
    # Section 4 - Logging and Auditing
    '4.1.1': {'package_name': 'audit'},
    '4.1.3': {'service_name': 'auditd', 'expected_status': 'active'},
    '4.1.4': {'file_path': '/etc/audit/auditd.conf', 'pattern': 'max_log_file_action', 'expected_result': 'present'},
    
    # Section 5 - Access Control
    '5.3.1.1': {'package_name': 'pam'},
    '5.3.1.2': {'package_name': 'authselect'},
    '5.4.1.5': {'file_path': '/etc/default/useradd', 'pattern': 'INACTIVE=30', 'expected_result': 'present'},
    '5.4.2.4': {'file_path': '/etc/login.defs', 'pattern': 'PASS_MIN_DAYS', 'expected_result': 'present'},
    '5.4.2.5': {'file_path': '/etc/login.defs', 'pattern': 'PASS_WARN_AGE', 'expected_result': 'present'},
    '5.4.2.6': {'file_path': '/etc/login.defs', 'pattern': 'PASS_MAX_DAYS', 'expected_result': 'present'},
    '5.4.3.2': {'file_path': '/etc/bashrc', 'pattern': 'TMOUT', 'expected_result': 'present'},
    
    # Section 6 - System Maintenance
    '6.2.1.1.1': {'file_path': '/etc/ssh/sshd_config', 'pattern': 'Protocol 2', 'expected_result': 'present'},
    '6.2.1.1.4': {'file_path': '/etc/ssh/sshd_config', 'pattern': 'PermitRootLogin no', 'expected_result': 'present'},
    '6.2.1.1.5': {'file_path': '/etc/ssh/sshd_config', 'pattern': 'PermitEmptyPasswords no', 'expected_result': 'present'},
    '6.2.1.1.6': {'file_path': '/etc/ssh/sshd_config', 'pattern': 'PermitUserEnvironment no', 'expected_result': 'present'},
    '6.2.1.2.1': {'package_name': 'rsyslog'},
    '6.2.1.2.3': {'service_name': 'rsyslog', 'expected_status': 'active'},
    '6.2.1.2.4': {'service_name': 'rsyslog', 'expected_status': 'enabled'},
    '6.2.2.1': {'package_name': 'systemd-journal-remote'},
    '6.2.2.2': {'service_name': 'systemd-journal-upload', 'expected_status': 'active'},
    '6.2.2.3': {'file_path': '/etc/systemd/journal-upload.conf', 'pattern': 'URL=', 'expected_result': 'present'},
    '6.2.3.1': {'file_path': '/etc/systemd/journald.conf', 'pattern': 'Storage=persistent', 'expected_result': 'present'},
    
    # Section 6.3 - File Permissions
    '6.3.1.1': {'file_path': '/etc/passwd', 'expected_permissions': '0644', 'expected_owner': 'root', 'expected_group': 'root'},
    '6.3.1.4': {'service_name': 'systemd-coredump', 'expected_status': 'inactive'},
    '6.3.2.1': {'file_path': '/etc/shadow', 'expected_permissions': '0000', 'expected_owner': 'root', 'expected_group': 'root'},
    '6.3.2.2': {'file_path': '/etc/gshadow', 'expected_permissions': '0000', 'expected_owner': 'root', 'expected_group': 'root'},
    '6.3.2.3': {'file_path': '/etc/group', 'expected_permissions': '0644', 'expected_owner': 'root', 'expected_group': 'root'},
    '6.3.2.4': {'file_path': '/etc/passwd-', 'expected_permissions': '0600', 'expected_owner': 'root', 'expected_group': 'root'},
    '6.3.3.2': {'file_path': '/etc/motd', 'expected_permissions': '0644', 'expected_owner': 'root', 'expected_group': 'root'},
    '6.3.3.3': {'file_path': '/etc/issue', 'expected_permissions': '0644', 'expected_owner': 'root', 'expected_group': 'root'},
    '6.3.3.6': {'file_path': '/etc/issue.net', 'expected_permissions': '0644', 'expected_owner': 'root', 'expected_group': 'root'},
    '6.3.3.7': {'file_path': '/etc/hosts.allow', 'expected_permissions': '0644', 'expected_owner': 'root', 'expected_group': 'root'},
    '6.3.3.10': {'file_path': '/etc/hosts.deny', 'expected_permissions': '0644', 'expected_owner': 'root', 'expected_group': 'root'},
    '6.3.3.11': {'file_path': '/etc/sysctl.conf', 'expected_permissions': '0600', 'expected_owner': 'root', 'expected_group': 'root'},
    '6.3.3.13': {'file_path': '/etc/sysctl.d', 'expected_permissions': '0755', 'expected_owner': 'root', 'expected_group': 'root'},
    '6.3.3.21': {'file_path': '/etc/ssh/sshd_config', 'expected_permissions': '0600', 'expected_owner': 'root', 'expected_group': 'root'},
    '6.3.4.1': {'file_path': '/etc/ssh/ssh_host_rsa_key', 'expected_permissions': '0600', 'expected_owner': 'root', 'expected_group': 'root'},
    '6.3.4.2': {'file_path': '/etc/ssh/ssh_host_ecdsa_key', 'expected_permissions': '0600', 'expected_owner': 'root', 'expected_group': 'root'},
    '6.3.4.3': {'file_path': '/etc/ssh/ssh_host_ed25519_key', 'expected_permissions': '0600', 'expected_owner': 'root', 'expected_group': 'root'},
    '6.3.4.4': {'file_path': '/etc/ssh/ssh_host_rsa_key.pub', 'expected_permissions': '0644', 'expected_owner': 'root', 'expected_group': 'root'},
    '6.3.4.5': {'file_path': '/etc/ssh/ssh_host_ecdsa_key.pub', 'expected_permissions': '0644', 'expected_owner': 'root', 'expected_group': 'root'},
    '6.3.4.6': {'file_path': '/etc/ssh/ssh_host_ed25519_key.pub', 'expected_permissions': '0644', 'expected_owner': 'root', 'expected_group': 'root'},
    '6.3.4.7': {'file_path': '/etc/at.allow', 'expected_permissions': '0600', 'expected_owner': 'root', 'expected_group': 'root'},
    '6.3.4.8': {'file_path': '/etc/at.deny', 'expected_permissions': '0600', 'expected_owner': 'root', 'expected_group': 'root'},
    '6.3.4.9': {'file_path': '/etc/cron.allow', 'expected_permissions': '0600', 'expected_owner': 'root', 'expected_group': 'root'},
    '6.3.4.10': {'file_path': '/etc/cron.deny', 'expected_permissions': '0600', 'expected_owner': 'root', 'expected_group': 'root'},
    
    # Section 7 - User Accounts
    '7.1.11': {'file_path': '/etc/login.defs', 'pattern': 'UMASK', 'expected_result': 'present'},
    '7.2.9': {'file_path': '/etc/profile', 'pattern': 'TMOUT', 'expected_result': 'present'},
}

def fix_milestone_file(filepath):
    """Fix missing fields in a milestone file."""
    with open(filepath, 'r') as f:
        data = json.load(f)
    
    modified = False
    for ctrl in data.get('controls', []):
        if not ctrl.get('automated', False):
            continue
        
        ctrl_id = ctrl.get('id')
        if ctrl_id in MANUAL_MAPPINGS:
            # Add missing fields from manual mapping
            for key, value in MANUAL_MAPPINGS[ctrl_id].items():
                if key not in ctrl or not ctrl[key]:
                    ctrl[key] = value
                    modified = True
                    print(f"  ✓ {ctrl_id}: Added {key}={value}")
    
    if modified:
        # Write back to file
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        return True
    return False

def main():
    print("=" * 80)
    print("FIXING MISSING FIELDS IN MILESTONE FILES")
    print("=" * 80)
    
    milestone_files = sorted(glob.glob('milestones/milestone-*.json'))
    total_fixed = 0
    
    for filepath in milestone_files:
        filename = os.path.basename(filepath)
        print(f"\n📄 Processing {filename}...")
        if fix_milestone_file(filepath):
            total_fixed += 1
    
    print(f"\n{'=' * 80}")
    print(f"✅ Fixed {total_fixed} milestone files")
    print(f"{'=' * 80}")

if __name__ == '__main__':
    main()
