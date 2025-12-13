#!/bin/bash

# CIS Control Verification Script
# This script checks actual system state for key controls
# Compare output with scanner results to find false positives/negatives

echo "================================================================================"
echo "CIS CONTROL VERIFICATION - RHEL 8"
echo "================================================================================"
echo "Server: $(hostname)"
echo "Date: $(date)"
echo ""

# Function to print control result
print_control() {
    local id="$1"
    local title="$2"
    local actual="$3"
    echo "[$id] $title"
    echo "  Actual: $actual"
    echo ""
}

echo "================================================================================"
echo "1. KERNEL MODULES"
echo "================================================================================"

print_control "1.1.1.1" "cramfs module" "$(lsmod | grep cramfs || echo 'not loaded')"
echo "  Blacklisted: $(grep -r 'install cramfs' /etc/modprobe.d/ 2>/dev/null || echo 'NO')"
echo ""

print_control "1.1.1.10" "usb-storage module" "$(lsmod | grep usb_storage || echo 'not loaded')"
echo "  Blacklisted: $(grep -r 'install usb.storage' /etc/modprobe.d/ 2>/dev/null || echo 'NO')"
echo ""

echo "================================================================================"
echo "2. MOUNT POINTS & OPTIONS"
echo "================================================================================"

print_control "1.1.2.1.1" "/tmp partition" "$(findmnt /tmp || echo 'NOT SEPARATE')"
echo ""

print_control "1.1.2.1.2-4" "/tmp mount options" "$(mount | grep ' /tmp ' || echo 'N/A')"
echo ""

print_control "1.1.2.2.4" "/dev/shm noexec" "$(mount | grep /dev/shm | grep -o 'noexec' || echo 'MISSING')"
echo ""

print_control "1.1.2.3" "/home partition" "$(findmnt /home || echo 'NOT SEPARATE')"
echo ""

print_control "1.1.2.4" "/var partition" "$(findmnt /var || echo 'NOT SEPARATE')"
echo ""

echo "================================================================================"
echo "3. SELINUX"
echo "================================================================================"

print_control "1.3.1.1" "SELinux installed" "$(rpm -q libselinux)"
echo ""

print_control "1.3.1.2" "SELinux in grub" "$(grep -E 'selinux=0|enforcing=0' /etc/default/grub 2>/dev/null || echo 'NOT DISABLED')"
echo ""

print_control "1.3.1.3" "SELinux policy" "$(grep '^SELINUXTYPE=' /etc/selinux/config 2>/dev/null || echo 'NOT SET')"
echo ""

print_control "1.3.1.4" "SELinux mode" "$(grep '^SELINUX=' /etc/selinux/config 2>/dev/null || echo 'NOT SET')"
echo "  Current: $(getenforce 2>/dev/null || echo 'N/A')"
echo ""

print_control "1.3.1.7" "mcstrans package" "$(rpm -q mcstrans 2>&1)"
echo ""

print_control "1.3.1.8" "setroubleshoot package" "$(rpm -q setroubleshoot 2>&1)"
echo ""

echo "================================================================================"
echo "4. BOOTLOADER"
echo "================================================================================"

print_control "1.4.1" "Bootloader password" "$(grep -c 'password_pbkdf2' /boot/grub2/grub.cfg 2>/dev/null || echo '0')"
echo ""

print_control "1.4.2" "Bootloader config perms" "$(stat -c '%a %U:%G' /boot/grub2/grub.cfg 2>/dev/null || echo 'N/A')"
echo ""

echo "================================================================================"
echo "5. FILE PERMISSIONS"
echo "================================================================================"

print_control "1.7.5" "/etc/issue perms" "$(stat -c '%a %U:%G' /etc/issue 2>/dev/null || echo 'N/A')"
echo ""

print_control "1.7.6" "/etc/issue.net perms" "$(stat -c '%a %U:%G' /etc/issue.net 2>/dev/null || echo 'N/A')"
echo ""

print_control "2.4.1.2" "/etc/crontab perms" "$(stat -c '%a %U:%G' /etc/crontab 2>/dev/null || echo 'N/A')"
echo ""

echo "================================================================================"
echo "6. SERVICES"
echo "================================================================================"

print_control "2.1.1" "autofs service" "$(systemctl is-enabled autofs 2>&1) / $(systemctl is-active autofs 2>&1)"
echo ""

print_control "2.1.2" "avahi-daemon service" "$(systemctl is-enabled avahi-daemon 2>&1) / $(systemctl is-active avahi-daemon 2>&1)"
echo ""

print_control "2.4.1.1" "cron service" "$(systemctl is-enabled crond 2>&1) / $(systemctl is-active crond 2>&1)"
echo ""

echo "================================================================================"
echo "7. PACKAGES"
echo "================================================================================"

print_control "1.12.1" "AIDE installed" "$(rpm -q aide 2>&1)"
echo ""

print_control "2.1.8" "dovecot package" "$(rpm -q dovecot 2>&1)"
echo ""

print_control "2.1.19" "httpd package" "$(rpm -q httpd 2>&1)"
echo ""

echo "================================================================================"
echo "8. SYSCTL PARAMETERS"
echo "================================================================================"

print_control "1.5.5" "kernel.dmesg_restrict" "$(sysctl kernel.dmesg_restrict 2>/dev/null || echo 'NOT SET')"
echo ""

print_control "1.5.6" "kernel.kptr_restrict" "$(sysctl kernel.kptr_restrict 2>/dev/null || echo 'NOT SET')"
echo ""

print_control "3.3.1" "net.ipv4.ip_forward" "$(sysctl net.ipv4.ip_forward 2>/dev/null || echo 'NOT SET')"
echo ""

echo "================================================================================"
echo "SUMMARY"
echo "================================================================================"
echo "Compare this output with scanner results to identify:"
echo "  - False Positives: Scanner shows FAIL but actual state is correct"
echo "  - False Negatives: Scanner shows PASS but actual state is incorrect"
echo ""
echo "Save this output and send along with scanner CSV/HTML reports"
echo "================================================================================"
