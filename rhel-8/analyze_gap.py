#!/usr/bin/env python3
"""
Smart analysis to find the 60 missing automated controls
by comparing OpenSCAP automated controls with our MANUAL controls
"""

# OpenSCAP automated controls from the report
openscap_controls = [
    # Software Integrity
    "Install AIDE",
    "Build and Test AIDE Database", 
    "Configure AIDE to Verify the Audit Tools",
    "Configure Periodic Execution of AIDE",
    "Configure System Cryptography Policy",
    
    # Disk Partitioning
    "Ensure /tmp Located On Separate Partition",
    
    # Sudo
    "Ensure Only Users Logged In To Real tty Can Execute Sudo - sudo use_pty",
    "Ensure Sudo Logfile Exists - sudo logfile", 
    "Ensure Users Re-Authenticate for Privilege Escalation - sudo",
    "Require Re-Authentication When Using the sudo Command",
    
    # Warning Banners
    "Ensure Local Login Warning Banner Is Configured Properly",
    "Ensure Remote Login Warning Banner Is Configured Properly",
    
    # PAM Controls (12 controls)
    "Configure the Use of the pam_faillock.so Module in the /etc/pam.d/password-auth File",
    "Configure the Use of the pam_faillock.so Module in the /etc/pam.d/system-auth File", 
    "Limit Password Reuse: password-auth",
    "Limit Password Reuse: system-auth",
    "Lock Accounts After Failed Password Attempts",
    "Set Lockout Time for Failed Password Attempts",
    "Ensure PAM Enforces Password Requirements - Prevent the Use of Dictionary Words",
    "Ensure PAM Enforces Password Requirements - Minimum Different Characters",
    "Ensure PAM Enforces Password Requirements - Enforce for root User", 
    "Set Password Maximum Consecutive Repeating Characters",
    "Ensure PAM Enforces Password Requirements - Minimum Different Categories",
    "Ensure PAM Enforces Password Requirements - Minimum Length",
    
    # Account Controls
    "Set Account Expiration Following Inactivity",
    "Set Password Maximum Age",
    "Prevent Login to Accounts With Empty Password",
    "Ensure the Group Used by pam_wheel.so Module Exists on System and is Empty",
    "Ensure Authentication Required for Single User Mode", 
    "Enforce Usage of pam_wheel with Group Parameter for su Authentication",
    
    # Session Configuration
    "Ensure the Default Bash Umask is Set Correctly",
    "Ensure the Default Umask is Set Correctly in login.defs",
    "Ensure the Default Umask is Set Correctly in /etc/profile",
    "Set Interactive Session Timeout",
    "Ensure All User Initialization Files Have Mode 0740 Or Less Permissive",
    
    # GRUB2 bootloader
    "Set the UEFI Boot Loader Password",
    
    # Syslog
    "Ensure System Log Files Have Correct Permissions",
    "Ensure journald is configured to compress large log files",
    "Ensure journald is configured to send logs to rsyslog", 
    "Ensure journald is configured to write log files to persistent disk",
    "Ensure rsyslog Default File Permissions Configured",
    
    # Firewall
    "Install firewalld Package",
    "Configure Firewalld to Restrict Loopback Traffic",
    "Configure Firewalld to Trust Loopback Traffic",
    
    # IPv6 (7 controls)
    "Configure Accepting Router Advertisements on All IPv6 Interfaces",
    "Disable Accepting ICMP Redirects for All IPv6 Interfaces",
    "Disable Kernel Parameter for Accepting Source-Routed Packets on all IPv6 Interfaces",
    "Disable Kernel Parameter for IPv6 Forwarding", 
    "Disable Accepting Router Advertisements on all IPv6 Interfaces by Default",
    "Disable Kernel Parameter for Accepting ICMP Redirects by Default on IPv6 Interfaces",
    "Disable Kernel Parameter for Accepting Source-Routed Packets on IPv6 Interfaces by Default",
    
    # Network Parameters (11 controls)
    "Disable Accepting ICMP Redirects for All IPv4 Interfaces",
    "Enable Kernel Parameter to Log Martian Packets on all IPv4 Interfaces",
    "Disable Kernel Parameter for Accepting Secure ICMP Redirects on all IPv4 Interfaces",
    "Disable Kernel Parameter for Accepting ICMP Redirects by Default on IPv4 Interfaces",
    "Disable Kernel Parameter for Accepting Source-Routed Packets on IPv4 Interfaces by Default",
    "Enable Kernel Paremeter to Log Martian Packets on all IPv4 Interfaces by Default", 
    "Enable Kernel Parameter to Use Reverse Path Filtering on all IPv4 Interfaces by Default",
    "Configure Kernel Parameter for Accepting Secure Redirects By Default",
    "Enable Kernel Parameter to Ignore ICMP Broadcast Echo Requests on IPv4 Interfaces",
    "Enable Kernel Parameter to Ignore Bogus ICMP Error Responses on IPv4 Interfaces",
    "Enable Kernel Parameter to Use TCP Syncookies on Network Interfaces",
    "Disable Kernel Parameter for Sending ICMP Redirects on all IPv4 Interfaces",
    "Disable Kernel Parameter for Sending ICMP Redirects on all IPv4 Interfaces by Default", 
    "Disable Kernel Parameter for IP Forwarding on IPv4 Interfaces",
    
    # nftables
    "Install nftables Package",
    
    # File Permissions
    "Verify that All World-Writable Directories Have Sticky Bits Set",
    "Ensure No World-Writable Files Exist",
    "Disable Mounting of cramfs",
    "Disable Modprobe Loading of USB Storage Driver",
    
    # Mount Options (3 controls for /dev/shm)
    "Add nodev Option to /dev/shm",
    "Add noexec Option to /dev/shm", 
    "Add nosuid Option to /dev/shm",
    
    # Core Dumps
    "Disable core dump backtraces",
    "Disable storing core dump",
    "Enable Randomized Layout of Virtual Address Space",
    "Restrict usage of ptrace to descendant processes",
    
    # SELinux
    "Ensure SELinux is Not Disabled",
    
    # Cron (6 controls)
    "Ensure that /etc/cron.allow exists",
    "Ensure that /etc/cron.deny does not exist", 
    "Verify Permissions on cron.d",
    "Verify Permissions on cron.daily",
    "Verify Permissions on cron.hourly",
    "Verify Permissions on cron.monthly",
    "Verify Permissions on cron.weekly", 
    "Verify Permissions on crontab",
    
    # Telnet
    "Remove telnet Clients",
    
    # SSH (17 controls)
    "Set SSH Client Alive Count Max",
    "Set SSH Client Alive Interval",
    "Disable Host-Based Authentication",
    "Disable SSH Access via Empty Passwords",
    "Disable SSH Support for .rhosts Files", 
    "Disable SSH Root Login",
    "Do Not Allow SSH Environment Options",
    "Enable SSH Warning Banner",
    "Limit Users' SSH Access",
    "Ensure SSH LoginGraceTime is configured",
    "Set SSH Daemon LogLevel to VERBOSE",
    "Set SSH authentication attempt limit",
    "Set SSH MaxSessions limit", 
    "Ensure SSH MaxStartups is configured",
    "Use Only FIPS 140-2 Validated Ciphers",
    "Use Only Strong Key Exchange algorithms",
    "Use Only Strong MACs"
]

# Our MANUAL controls from Vijenex scan results
vijenex_manual_controls = [
    "1.10.1 Ensure message of the day is configured properly",
    "1.10.2 Ensure local login warning banner is configured properly", 
    "1.10.3 Ensure remote login warning banner is configured properly",
    "1.10.4 Ensure permissions on /etc/motd are configured",
    "1.10.5 Ensure permissions on /etc/issue are configured",
    "1.10.6 Ensure permissions on /etc/issue.net are configured",
    "1.11.1 Ensure system-wide crypto policy is not legacy",
    "1.12.1 Ensure AIDE is installed",
    "1.12.2 Ensure filesystem integrity is regularly checked",
    "1.2.1.1 Ensure GPG keys are configured",
    "1.2.1.3 Ensure repo_gpgcheck is globally activated", 
    "1.2.1.4 Ensure package manager repositories are configured",
    "1.3.1.6 Ensure no unconfined services exist",
    "1.7.1 Ensure SELinux is installed",
    "1.7.2 Ensure SELinux is not disabled in bootloader configuration",
    "1.7.3 Ensure SELinux policy is configured",
    "1.7.4 Ensure the SELinux mode is enforcing or permissive",
    "1.8.1 Ensure GNOME Display Manager is removed",
    "1.8.2 Ensure GDM login banner is configured",
    "1.8.3 Ensure GDM disable-user-list option is enabled",
    "1.8.4 Ensure GDM screen locks when the user is idle",
    "1.8.5 Ensure GDM screen locks cannot be overridden", 
    "1.8.6 Ensure GDM automatic mounting of removable media is disabled",
    "1.9.1 Ensure system-wide crypto policy is not legacy",
    "1.9.2 Ensure system-wide crypto policy is FUTURE or FIPS",
    "2.2.14 Ensure mail transfer agent is configured for local-only mode",
    "2.5.1 Ensure NFS is not installed",
    "2.5.2 Ensure rpcbind is not installed", 
    "2.5.3 Ensure rsync is not installed",
    "3.1.1 Ensure IPv6 status is identified",
    "3.4.1.5 Ensure firewalld default zone is set",
    "3.4.1.6 Ensure network interfaces are assigned to appropriate zone",
    "3.4.1.7 Ensure firewalld drops unnecessary services and ports",
    "3.5.1 Ensure DCCP is disabled",
    "3.5.2 Ensure SCTP is disabled",
    "3.5.3 Ensure RDS is disabled",
    "3.5.4 Ensure TIPC is disabled",
    "3.6.1 Ensure iptables packages are installed",
    "3.6.2 Ensure nftables is not installed with iptables",
    "3.6.3 Ensure firewalld is not installed with iptables",
    "4.1.1.1 Ensure auditd is installed",
    "4.1.1.2 Ensure auditd service is enabled and running",
    "4.1.1.3 Ensure auditing for processes that start prior to auditd is enabled",
    "4.1.1.4 Ensure audit_backlog_limit is sufficient",
    "4.1.2.1 Ensure audit log storage size is configured",
    "4.1.2.2 Ensure audit logs are not automatically deleted",
    "4.1.2.3 Ensure system is disabled when audit logs are full",
    "4.1.3.1 Ensure changes to system administration scope (sudoers) is collected",
    "4.1.3.2 Ensure actions as another user are always logged",
    "4.1.3.3 Ensure events that modify date and time information are collected",
    "4.1.3.4 Ensure events that modify the system's network environment are collected",
    "4.1.3.5 Ensure events that modify the system's Mandatory Access Controls are collected",
    "4.1.3.6 Ensure login and logout events are collected",
    "4.1.3.7 Ensure session initiation information is collected",
    "4.1.3.8 Ensure discretionary access control permission modification events are collected",
    "4.1.3.9 Ensure unsuccessful file access attempts are collected",
    "4.1.3.10 Ensure successful file system mounts are collected",
    "4.1.3.11 Ensure file deletion events by users are collected",
    "4.1.3.12 Ensure changes to system administration scope (sudoers) is collected",
    "4.1.3.13 Ensure system administrator command executions (sudo) are collected",
    "4.1.3.14 Ensure kernel module loading and unloading is collected",
    "4.1.3.15 Ensure the audit configuration is immutable",
    "4.1.5 Ensure firewalld loopback traffic is configured",
    "4.1.7 Ensure firewalld services and ports are configured",
    "4.2.1.3 Ensure journald is configured to send logs to rsyslog",
    "4.2.1.4 Ensure rsyslog default file permissions are configured",
    "4.2.1.5 Ensure logging is configured",
    "4.2.1.6 Ensure rsyslog is not configured to receive logs from a remote client",
    "4.3.1 Ensure logrotate is configured",
    "4.3.2 Ensure logrotate assigns appropriate permissions",
    "4.4.1 Ensure rsyslog is installed",
    "4.4.2 Ensure journald is configured to send logs to rsyslog",
    "4.4.3 Ensure journald is configured to compress large log files",
    "4.4.4 Ensure journald is configured to write logfiles to persistent disk",
    "5.1.2 Ensure permissions on SSH private host key files are configured",
    "5.1.3 Ensure permissions on SSH public host key files are configured",
    "5.1.4 Ensure sshd access is configured",
    "5.1.5 Ensure sshd Banner is configured",
    "5.1.6 Ensure sshd Ciphers are configured",
    "5.1.7 Ensure sshd ClientAliveInterval and ClientAliveCountMax are configured",
    "5.1.8 Ensure sshd DisableForwarding is enabled",
    "5.1.9 Ensure sshd HostbasedAuthentication is disabled",
    "5.1.10 Ensure sshd IgnoreRhosts is enabled",
    "5.2.1 Ensure permissions on SSH private host key files are configured",
    "5.2.2 Ensure permissions on SSH public host key files are configured",
    "5.2.3 Ensure permissions on SSH public host key files are configured",
    "5.2.4 Ensure SSH access is limited",
    "5.2.5 Ensure SSH LogLevel is appropriate",
    "5.2.6 Ensure SSH X11 forwarding is disabled",
    "5.2.7 Ensure SSH MaxAuthTries is set to 4 or less",
    "5.2.8 Ensure SSH IgnoreRhosts is enabled",
    "5.2.9 Ensure SSH HostbasedAuthentication is disabled",
    "5.2.10 Ensure SSH root login is disabled",
    "5.2.11 Ensure SSH PermitEmptyPasswords is disabled",
    "5.2.12 Ensure SSH PermitUserEnvironment is disabled",
    "5.2.13 Ensure only strong Ciphers are used",
    "5.2.14 Ensure only strong MAC algorithms are used",
    "5.2.15 Ensure only strong Key Exchange algorithms are used",
    "5.2.16 Ensure SSH Idle Timeout Interval is configured",
    "5.2.17 Ensure SSH LoginGraceTime is set to one minute or less",
    "5.2.18 Ensure SSH warning banner is configured",
    "5.2.19 Ensure SSH PAM is enabled",
    "5.2.20 Ensure SSH AllowTcpForwarding is disabled",
    "5.2.21 Ensure SSH MaxStartups is configured",
    "5.2.22 Ensure SSH MaxSessions is set to 10 or less",
    "5.2.2 Ensure sudo commands use pty",
    "5.2.3 Ensure sudo log file exists",
    "5.2.4 Ensure users must provide password for privilege escalation",
    "5.2.5 Ensure re-authentication for privilege escalation is not disabled globally",
    "5.2.6 Ensure sudo authentication timeout is configured correctly",
    "5.2.7 Ensure access to the su command is restricted",
    "5.3.1 Ensure password creation requirements are configured",
    "5.3.2 Ensure lockout for failed password attempts is configured",
    "5.3.3 Ensure password reuse is limited",
    "5.3.3.2.3 Ensure password complexity is configured",
    "5.4.1 Ensure password expiration is 365 days or less",
    "5.4.1.2 Ensure minimum password days is configured",
    "5.4.2 Ensure minimum days between password changes is configured",
    "5.4.3 Ensure password expiration warning days is 7 or more",
    "5.4.4 Ensure inactive password lock is 30 days or less",
    "5.4.5 Ensure default user shell timeout is configured",
    "5.4.6 Ensure default user umask is configured",
    "5.5.1 Ensure default user shell timeout is 900 seconds or less",
    "5.5.2 Ensure default user umask is 027 or more restrictive",
    "5.5.3 Ensure default group for the root account is GID 0",
    "5.5.4 Ensure default user shell timeout is configured",
    "5.6.1 Ensure access to the su command is restricted",
    "5.7.1 Ensure password expiration is 365 days or less",
    "5.7.2 Ensure minimum days between password changes is configured",
    "5.7.3 Ensure password expiration warning days is 7 or more",
    "5.7.4 Ensure inactive password lock is 30 days or less",
    "5.7.5 Ensure all users last password change date is in the past",
    "5.8.1 Ensure password creation requirements are configured",
    "5.8.2 Ensure lockout for failed password attempts is configured",
    "5.8.3 Ensure password reuse is limited",
    "5.8.4 Ensure password hashing algorithm is SHA-512",
    "6.1.9 Ensure no world writable files exist",
    "6.1.10 Ensure no unowned files or directories exist",
    "6.1.11 Ensure no ungrouped files or directories exist",
    "6.1.12 Ensure sticky bit is set on all world-writable directories",
    "6.2.1 Ensure accounts in /etc/passwd use shadowed passwords",
    "6.2.1.1.2 Ensure journald log file access is configured",
    "6.2.1.1.3 Ensure journald log file rotation is configured",
    "6.2.2.5 Ensure rsyslog logging is configured",
    "6.2.2.8 Ensure logrotate is configured",
    "6.2.3 Ensure all groups in /etc/passwd exist in /etc/group",
    "6.2.4 Ensure no duplicate UIDs exist",
    "6.2.5 Ensure no duplicate GIDs exist",
    "6.2.6 Ensure no duplicate user names exist",
    "6.2.7 Ensure no duplicate group names exist",
    "6.2.8 Ensure root PATH Integrity",
    "6.2.9 Ensure all users' home directories exist",
    "6.2.10 Ensure users own their home directories",
    "6.3.1 Ensure permissions on /etc/passwd- are configured",
    "6.3.2 Ensure permissions on /etc/group- are configured",
    "6.3.3 Ensure permissions on /etc/shadow- are configured",
    "6.3.3.22 Ensure the running and on disk configuration is the same",
    "6.3.4 Ensure permissions on /etc/gshadow- are configured",
    "6.3.5 Ensure no world writable files exist",
    "6.3.6 Ensure no unowned files or directories exist",
    "6.3.7 Ensure no ungrouped files or directories exist",
    "6.4.1 Ensure password fields are not empty",
    "6.4.2 Ensure all groups in /etc/passwd exist in /etc/group",
    "6.4.3 Ensure no duplicate UIDs exist",
    "6.4.4 Ensure no duplicate GIDs exist",
    "6.4.5 Ensure no duplicate user names exist",
    "6.4.6 Ensure no duplicate group names exist",
    "6.4.7 Ensure root PATH Integrity",
    "6.4.8 Ensure root is the only UID 0 account",
    "6.5.1 Ensure permissions on /etc/crontab are configured",
    "6.5.2 Ensure permissions on /etc/cron.hourly are configured",
    "6.5.3 Ensure permissions on /etc/cron.daily are configured",
    "6.5.4 Ensure permissions on /etc/cron.weekly are configured",
    "6.5.5 Ensure permissions on /etc/cron.monthly are configured",
    "6.5.6 Ensure permissions on /etc/cron.d are configured",
    "7.1.13 Ensure SUID and SGID files are reviewed"
]

def find_matching_controls():
    """Find controls that OpenSCAP automates but we mark as MANUAL"""
    
    # Create mapping keywords for matching
    openscap_keywords = {}
    for control in openscap_controls:
        # Extract key terms
        keywords = []
        if "AIDE" in control:
            keywords.append("AIDE")
        if "sudo" in control.lower():
            keywords.append("sudo")
        if "SSH" in control or "ssh" in control.lower():
            keywords.append("SSH")
        if "PAM" in control or "password" in control.lower():
            keywords.append("PAM")
        if "firewall" in control.lower():
            keywords.append("firewall")
        if "IPv6" in control or "IPv4" in control:
            keywords.append("network")
        if "cron" in control.lower():
            keywords.append("cron")
        if "banner" in control.lower():
            keywords.append("banner")
        if "umask" in control.lower():
            keywords.append("umask")
        if "SELinux" in control:
            keywords.append("SELinux")
        if "journald" in control.lower():
            keywords.append("journald")
        if "rsyslog" in control.lower():
            keywords.append("rsyslog")
            
        openscap_keywords[control] = keywords
    
    # Find matches
    matches = []
    for openscap_control in openscap_controls:
        keywords = openscap_keywords[openscap_control]
        for vijenex_control in vijenex_manual_controls:
            for keyword in keywords:
                if keyword.lower() in vijenex_control.lower():
                    matches.append({
                        'openscap': openscap_control,
                        'vijenex': vijenex_control,
                        'keyword': keyword
                    })
                    break
    
    return matches

def categorize_missing_controls():
    """Categorize the missing automated controls"""
    
    categories = {
        'AIDE': [],
        'SSH': [],
        'PAM/Password': [],
        'Firewall': [],
        'Network': [],
        'Cron': [],
        'Banner': [],
        'Umask': [],
        'Journald/Rsyslog': [],
        'File Permissions': [],
        'Other': []
    }
    
    for control in openscap_controls:
        if "AIDE" in control:
            categories['AIDE'].append(control)
        elif "SSH" in control or "ssh" in control.lower():
            categories['SSH'].append(control)
        elif "PAM" in control or "password" in control.lower() or "sudo" in control.lower():
            categories['PAM/Password'].append(control)
        elif "firewall" in control.lower():
            categories['Firewall'].append(control)
        elif "IPv6" in control or "IPv4" in control or "network" in control.lower():
            categories['Network'].append(control)
        elif "cron" in control.lower():
            categories['Cron'].append(control)
        elif "banner" in control.lower():
            categories['Banner'].append(control)
        elif "umask" in control.lower():
            categories['Umask'].append(control)
        elif "journald" in control.lower() or "rsyslog" in control.lower():
            categories['Journald/Rsyslog'].append(control)
        elif "permission" in control.lower() or "writable" in control.lower():
            categories['File Permissions'].append(control)
        else:
            categories['Other'].append(control)
    
    return categories

if __name__ == "__main__":
    print("🔍 SMART ANALYSIS: Finding the 60 Missing Automated Controls")
    print("=" * 70)
    
    matches = find_matching_controls()
    categories = categorize_missing_controls()
    
    print(f"\n📊 SUMMARY:")
    print(f"OpenSCAP Automated Controls: {len(openscap_controls)}")
    print(f"Vijenex Manual Controls: {len(vijenex_manual_controls)}")
    print(f"Potential Matches Found: {len(matches)}")
    
    print(f"\n🎯 TOP CATEGORIES TO AUTOMATE:")
    for category, controls in categories.items():
        if controls:
            print(f"{category}: {len(controls)} controls")
            for control in controls[:3]:  # Show first 3
                print(f"  - {control}")
            if len(controls) > 3:
                print(f"  ... and {len(controls)-3} more")
            print()
    
    print(f"\n🔗 DIRECT MATCHES (OpenSCAP automated → Vijenex manual):")
    for match in matches[:20]:  # Show first 20 matches
        print(f"✓ {match['keyword']}: {match['openscap']}")
        print(f"  → {match['vijenex']}")
        print()