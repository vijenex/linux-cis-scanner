#!/usr/bin/env python3
"""
██╗   ██╗██╗     ██╗███████╗███╗   ██╗███████╗██╗  ██╗
██║   ██║██║     ██║██╔════╝████╗  ██║██╔════╝╚██╗██╔╝
██║   ██║██║     ██║█████╗  ██╔██╗ ██║█████╗   ╚███╔╝ 
╚██╗ ██╔╝██║██   ██║██╔══╝  ██║╚██╗██║██╔══╝   ██╔██╗ 
 ╚████╔╝ ██║╚█████╔╝███████╗██║ ╚████║███████╗██╔╝ ██╗
  ╚═══╝  ╚═╝ ╚════╝ ╚══════╝╚═╝  ╚═══╝╚══════╝╚═╝  ╚═╝

                 Vijenex CIS Scanner
           Enterprise Linux Security Compliance
"""

import os
import sys
import json
import subprocess
import argparse
import datetime
import socket
import platform
import pwd
import grp
import stat
import re
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import glob

class LinuxCISScanner:
    """Main Linux CIS compliance scanner engine"""
    
    def __init__(self, output_dir: str = None, profile: str = "Level1"):
        # Use explicit output_dir if provided, otherwise use default
        if output_dir is None:
            output_dir = "./reports"
        
        self.output_dir = Path(output_dir)
        self.profile = profile
        self.results = []
        self.system_info = self._get_system_info()
        
        # Set milestones directory - use current script's milestones directory
        current_path = Path(__file__).parent
        self.milestones_dir = current_path.parent / "milestones"
        
        # Ensure output directory exists
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
    def _get_system_info(self) -> Dict[str, Any]:
        """Collect system information for reporting"""
        try:
            hostname = socket.gethostname()
            ip_address = socket.gethostbyname(hostname)
        except (socket.error, OSError) as e:
            hostname = "Unknown"
            ip_address = "Unknown"
            
        return {
            "hostname": hostname,
            "ip_address": ip_address,
            "os_name": platform.system(),
            "os_version": platform.release(),
            "distribution": self._get_distribution(),
            "architecture": platform.machine(),
            "scan_date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "scanner_version": "1.0.0"
        }
    
    def _get_distribution(self) -> str:
        """Get Linux distribution information"""
        try:
            with open('/etc/os-release', 'r') as f:
                for line in f:
                    if line.startswith('PRETTY_NAME='):
                        return line.split('=')[1].strip().strip('"')
        except:
            pass
        return "Unknown Linux Distribution"
    
    def _detect_ubuntu_version(self) -> str:
        """Detect Ubuntu version for directory selection"""
        try:
            with open('/etc/os-release', 'r') as f:
                for line in f:
                    if line.startswith('VERSION_ID='):
                        version = line.split('=')[1].strip().strip('"')
                        return version
        except (IOError, OSError, ValueError):
            pass
        return "24.04"  # Default fallback
    
    def _validate_path(self, file_path: str) -> bool:
        """Validate file path to prevent path traversal"""
        try:
            # Resolve path and check if it's within allowed directories
            resolved_path = os.path.realpath(file_path)
            allowed_prefixes = ['/etc/', '/var/', '/usr/', '/bin/', '/sbin/', '/lib/', '/opt/', '/home/', '/root/', '/proc/', '/sys/']
            return any(resolved_path.startswith(prefix) for prefix in allowed_prefixes)
        except (OSError, ValueError):
            return False
    
    def _run_command(self, command: str, shell: bool = True) -> Tuple[str, str, int]:
        """Execute system command and return output"""
        try:
            # Sanitize command for security
            if shell and isinstance(command, str):
                # Basic command validation - only allow known safe commands
                safe_commands = ['systemctl', 'sysctl', 'dpkg', 'rpm', 'lsmod', 'modinfo', 'aa-status', 'ufw', 'nft', 'ss', 'crontab', 'find', 'iwconfig', 'nmcli', 'rfkill']
                cmd_parts = command.split()
                if not cmd_parts or not any(safe_cmd in cmd_parts[0] for safe_cmd in safe_commands):
                    return "", "Command not allowed", 1
            
            result = subprocess.run(
                command,
                shell=shell,
                capture_output=True,
                text=True,
                timeout=30
            )
            return result.stdout, result.stderr, result.returncode
        except subprocess.TimeoutExpired:
            return "", "Command timeout", 1
        except (OSError, ValueError) as e:
            return "", f"Command error: {str(e)}", 1
        except Exception as e:
            return "", f"Unexpected error: {str(e)}", 1
    
    def check_file_permissions(self, file_path: str, expected_mode: str, expected_owner: str = None, expected_group: str = None) -> Dict[str, Any]:
        """Check file permissions and ownership"""
        try:
            # Validate path to prevent traversal attacks
            if not self._validate_path(file_path):
                return {
                    "status": "FAIL",
                    "current": "Invalid file path",
                    "expected": f"Mode: {expected_mode}, Owner: {expected_owner}, Group: {expected_group}",
                    "evidence": f"File path {file_path} is not allowed"
                }
            
            if not os.path.exists(file_path):
                return {
                    "status": "FAIL",
                    "current": "File not found",
                    "expected": f"Mode: {expected_mode}, Owner: {expected_owner}, Group: {expected_group}",
                    "evidence": f"File {file_path} does not exist"
                }
            
            file_stat = os.stat(file_path)
            current_mode = oct(file_stat.st_mode)[-3:]
            current_owner = pwd.getpwuid(file_stat.st_uid).pw_name
            current_group = grp.getgrgid(file_stat.st_gid).gr_name
            
            issues = []
            if expected_mode and current_mode != expected_mode:
                issues.append(f"Mode: {current_mode} (expected {expected_mode})")
            if expected_owner and current_owner != expected_owner:
                issues.append(f"Owner: {current_owner} (expected {expected_owner})")
            if expected_group and current_group != expected_group:
                issues.append(f"Group: {current_group} (expected {expected_group})")
            
            status = "PASS" if not issues else "FAIL"
            
            return {
                "status": status,
                "current": f"Mode: {current_mode}, Owner: {current_owner}, Group: {current_group}",
                "expected": f"Mode: {expected_mode}, Owner: {expected_owner}, Group: {expected_group}",
                "evidence": "; ".join(issues) if issues else "Permissions correct"
            }
            
        except (OSError, KeyError, ValueError) as e:
            return {
                "status": "FAIL",
                "current": "Error checking file",
                "expected": f"Mode: {expected_mode}, Owner: {expected_owner}, Group: {expected_group}",
                "evidence": f"File access error: {str(e)}"
            }
        except Exception as e:
            return {
                "status": "ERROR",
                "current": "Unexpected error",
                "expected": f"Mode: {expected_mode}, Owner: {expected_owner}, Group: {expected_group}",
                "evidence": f"Unexpected error: {str(e)}"
            }
    
    def check_service_status(self, service_name: str, expected_status: str) -> Dict[str, Any]:
        """Check systemd service status"""
        stdout, stderr, returncode = self._run_command(f"systemctl is-enabled {service_name}")
        enabled_status = stdout.strip()
        
        stdout, stderr, returncode = self._run_command(f"systemctl is-active {service_name}")
        active_status = stdout.strip()
        
        current_status = f"enabled={enabled_status}, active={active_status}"
        
        if expected_status == "disabled":
            status = "PASS" if enabled_status == "disabled" else "FAIL"
        elif expected_status == "enabled":
            status = "PASS" if enabled_status == "enabled" and active_status == "active" else "FAIL"
        else:
            status = "FAIL"
        
        return {
            "status": status,
            "current": current_status,
            "expected": expected_status,
            "evidence": f"Service {service_name}: {current_status}"
        }
    
    def check_kernel_parameter(self, parameter: str, expected_value: str) -> Dict[str, Any]:
        """Check kernel parameter value"""
        stdout, stderr, returncode = self._run_command(f"sysctl {parameter}")
        
        if returncode != 0:
            return {
                "status": "FAIL",
                "current": "Parameter not found",
                "expected": expected_value,
                "evidence": f"Kernel parameter {parameter} not found"
            }
        
        current_value = stdout.split('=')[1].strip() if '=' in stdout else stdout.strip()
        status = "PASS" if current_value == expected_value else "FAIL"
        
        return {
            "status": status,
            "current": current_value,
            "expected": expected_value,
            "evidence": f"{parameter} = {current_value}"
        }
    
    def check_package_installed(self, package_name: str, should_be_installed: bool = True) -> Dict[str, Any]:
        """Check if package is installed"""
        # Try dpkg first (Debian/Ubuntu)
        stdout, stderr, returncode = self._run_command(f"dpkg -l {package_name}")
        
        if returncode == 0 and "ii" in stdout:
            installed = True
        else:
            # Try rpm (RHEL/CentOS)
            stdout, stderr, returncode = self._run_command(f"rpm -q {package_name}")
            installed = returncode == 0
        
        if should_be_installed:
            status = "PASS" if installed else "FAIL"
            expected = "Installed"
        else:
            status = "PASS" if not installed else "FAIL"
            expected = "Not installed"
        
        current = "Installed" if installed else "Not installed"
        
        return {
            "status": status,
            "current": current,
            "expected": expected,
            "evidence": f"Package {package_name}: {current}"
        }
    
    def check_config_file(self, file_path: str, pattern: str, expected_match: bool = True) -> Dict[str, Any]:
        """Check configuration file for specific pattern"""
        try:
            # Validate path
            if not self._validate_path(file_path):
                return {
                    "status": "FAIL",
                    "current": "Invalid file path",
                    "expected": f"Pattern '{pattern}' {'found' if expected_match else 'not found'}",
                    "evidence": f"File path {file_path} is not allowed"
                }
            
            if not os.path.exists(file_path):
                return {
                    "status": "FAIL",
                    "current": "File not found",
                    "expected": f"Pattern '{pattern}' {'found' if expected_match else 'not found'}",
                    "evidence": f"Configuration file {file_path} does not exist"
                }
            
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            match_found = re.search(pattern, content, re.MULTILINE)
            
            if expected_match:
                status = "PASS" if match_found else "FAIL"
                expected = f"Pattern '{pattern}' found"
            else:
                status = "PASS" if not match_found else "FAIL"
                expected = f"Pattern '{pattern}' not found"
            
            current = f"Pattern {'found' if match_found else 'not found'}"
            
            return {
                "status": status,
                "current": current,
                "expected": expected,
                "evidence": f"In {file_path}: {current}"
            }
            
        except (OSError, IOError, UnicodeDecodeError) as e:
            return {
                "status": "FAIL",
                "current": "Error reading file",
                "expected": f"Pattern '{pattern}' {'found' if expected_match else 'not found'}",
                "evidence": f"File read error: {str(e)}"
            }
        except Exception as e:
            return {
                "status": "ERROR",
                "current": "Unexpected error",
                "expected": f"Pattern '{pattern}' {'found' if expected_match else 'not found'}",
                "evidence": f"Unexpected error: {str(e)}"
            }
    
    def check_kernel_module(self, module_name: str, expected_status: str) -> Dict[str, Any]:
        """Check kernel module availability and status"""
        try:
            # Check if module is blacklisted in modprobe.d
            blacklist_found = False
            modprobe_dirs = ['/etc/modprobe.d/', '/lib/modprobe.d/', '/usr/lib/modprobe.d/']
            
            for modprobe_dir in modprobe_dirs:
                if os.path.exists(modprobe_dir):
                    for conf_file in os.listdir(modprobe_dir):
                        if conf_file.endswith('.conf'):
                            conf_path = os.path.join(modprobe_dir, conf_file)
                            try:
                                with open(conf_path, 'r') as f:
                                    content = f.read()
                                    if re.search(f'install\s+{module_name}\s+/bin/(true|false)', content):
                                        blacklist_found = True
                                        break
                            except:
                                continue
                if blacklist_found:
                    break
            
            # Check if module is currently loaded
            stdout, stderr, returncode = self._run_command(f"lsmod | grep -w {module_name}")
            module_loaded = returncode == 0 and module_name in stdout
            
            # Check if module exists in the system
            stdout, stderr, returncode = self._run_command(f"modinfo {module_name}")
            module_exists = returncode == 0
            
            if expected_status == "not_available":
                if blacklist_found and not module_loaded:
                    status = "PASS"
                    current = "Module blacklisted and not loaded"
                elif not module_exists:
                    status = "PASS"
                    current = "Module not available in kernel"
                elif module_loaded:
                    status = "FAIL"
                    current = "Module is loaded"
                else:
                    status = "FAIL"
                    current = "Module available but not blacklisted"
            else:
                status = "FAIL"
                current = f"Unexpected expected_status: {expected_status}"
            
            return {
                "status": status,
                "current": current,
                "expected": f"Module {expected_status}",
                "evidence": f"Module {module_name}: blacklisted={blacklist_found}, loaded={module_loaded}, exists={module_exists}"
            }
            
        except Exception as e:
            return {
                "status": "ERROR",
                "current": "Error checking module",
                "expected": f"Module {expected_status}",
                "evidence": str(e)
            }
    
    def check_mount_option(self, mount_point: str, required_option: str) -> Dict[str, Any]:
        """Check if specific mount option is set for a mount point"""
        try:
            # Check /proc/mounts for current mount options
            current_options = []
            mount_found = False
            
            with open('/proc/mounts', 'r') as f:
                for line in f:
                    parts = line.strip().split()
                    if len(parts) >= 4 and parts[1] == mount_point:
                        mount_found = True
                        current_options = parts[3].split(',')
                        break
            
            if not mount_found:
                return {
                    "status": "FAIL",
                    "current": "Mount point not found",
                    "expected": f"Mount point {mount_point} with {required_option} option",
                    "evidence": f"Mount point {mount_point} is not mounted"
                }
            
            option_present = required_option in current_options
            status = "PASS" if option_present else "FAIL"
            
            return {
                "status": status,
                "current": f"Options: {','.join(current_options)}",
                "expected": f"Option '{required_option}' present",
                "evidence": f"Mount {mount_point}: {required_option} {'found' if option_present else 'missing'}"
            }
            
        except Exception as e:
            return {
                "status": "ERROR",
                "current": "Error checking mount options",
                "expected": f"Option '{required_option}' present",
                "evidence": str(e)
            }
    
    def check_mount_point(self, mount_point: str, expected_status: str) -> Dict[str, Any]:
        """Check if mount point is configured as separate partition"""
        try:
            # Check if mount point exists as separate partition
            mount_found = False
            device_info = ""
            
            with open('/proc/mounts', 'r') as f:
                for line in f:
                    parts = line.strip().split()
                    if len(parts) >= 2 and parts[1] == mount_point:
                        mount_found = True
                        device_info = parts[0]
                        break
            
            if expected_status == "separate_partition":
                if mount_found and not device_info.startswith('/dev/loop'):
                    status = "PASS"
                    current = f"Separate partition: {device_info}"
                elif mount_found:
                    status = "PASS"
                    current = f"Mounted (may be tmpfs): {device_info}"
                else:
                    status = "FAIL"
                    current = "Not a separate partition"
            else:
                status = "FAIL"
                current = f"Unexpected expected_status: {expected_status}"
            
            return {
                "status": status,
                "current": current,
                "expected": f"Mount point {expected_status}",
                "evidence": f"Mount point {mount_point}: {current}"
            }
            
        except Exception as e:
            return {
                "status": "ERROR",
                "current": "Error checking mount point",
                "expected": f"Mount point {expected_status}",
                "evidence": str(e)
            }
    
    def check_boot_parameters(self, parameters: List[str], config_file: str) -> Dict[str, Any]:
        """Check boot parameters in GRUB configuration"""
        try:
            if not os.path.exists(config_file):
                return {
                    "status": "FAIL",
                    "current": "Config file not found",
                    "expected": f"Parameters {parameters} in {config_file}",
                    "evidence": f"Boot config file {config_file} does not exist"
                }
            
            with open(config_file, 'r') as f:
                content = f.read()
            
            missing_params = []
            found_params = []
            
            for param in parameters:
                if param in content:
                    found_params.append(param)
                else:
                    missing_params.append(param)
            
            if not missing_params:
                status = "PASS"
                current = f"All parameters found: {', '.join(found_params)}"
            else:
                status = "FAIL"
                current = f"Missing: {', '.join(missing_params)}, Found: {', '.join(found_params)}"
            
            return {
                "status": status,
                "current": current,
                "expected": f"Parameters: {', '.join(parameters)}",
                "evidence": f"In {config_file}: {current}"
            }
            
        except Exception as e:
            return {
                "status": "ERROR",
                "current": "Error checking boot parameters",
                "expected": f"Parameters: {', '.join(parameters)}",
                "evidence": str(e)
            }
    
    def check_apparmor_profiles(self, expected_modes: List[str], check_unconfined: bool) -> Dict[str, Any]:
        """Check AppArmor profile status"""
        try:
            # Check if AppArmor is enabled
            stdout, stderr, returncode = self._run_command("aa-status --enabled")
            if returncode != 0:
                return {
                    "status": "FAIL",
                    "current": "AppArmor not enabled",
                    "expected": f"Profiles in modes: {', '.join(expected_modes)}",
                    "evidence": "AppArmor is not enabled on the system"
                }
            
            # Get profile status
            stdout, stderr, returncode = self._run_command("aa-status")
            if returncode != 0:
                return {
                    "status": "ERROR",
                    "current": "Cannot get AppArmor status",
                    "expected": f"Profiles in modes: {', '.join(expected_modes)}",
                    "evidence": f"aa-status failed: {stderr}"
                }
            
            # Parse aa-status output
            enforce_count = 0
            complain_count = 0
            unconfined_count = 0
            
            lines = stdout.split('\n')
            for line in lines:
                if 'profiles are in enforce mode' in line:
                    enforce_count = int(line.split()[0])
                elif 'profiles are in complain mode' in line:
                    complain_count = int(line.split()[0])
                elif 'processes are unconfined' in line:
                    unconfined_count = int(line.split()[0])
            
            total_profiles = enforce_count + complain_count
            
            if check_unconfined and unconfined_count > 0:
                status = "FAIL"
                current = f"Enforce: {enforce_count}, Complain: {complain_count}, Unconfined: {unconfined_count}"
            elif "enforce" in expected_modes and "complain" in expected_modes:
                # Both modes acceptable
                status = "PASS" if total_profiles > 0 else "FAIL"
                current = f"Enforce: {enforce_count}, Complain: {complain_count}"
            elif "enforce" in expected_modes and complain_count > 0:
                # Only enforce mode acceptable
                status = "FAIL"
                current = f"Enforce: {enforce_count}, Complain: {complain_count} (should be 0)"
            else:
                status = "PASS" if total_profiles > 0 else "FAIL"
                current = f"Enforce: {enforce_count}, Complain: {complain_count}"
            
            return {
                "status": status,
                "current": current,
                "expected": f"Profiles in modes: {', '.join(expected_modes)}",
                "evidence": f"AppArmor status: {current}"
            }
            
        except Exception as e:
            return {
                "status": "ERROR",
                "current": "Error checking AppArmor profiles",
                "expected": f"Profiles in modes: {', '.join(expected_modes)}",
                "evidence": str(e)
            }
    
    def check_core_dump_restriction(self, expected_setting: str, limits_files: List[str]) -> Dict[str, Any]:
        """Check core dump restrictions in limits configuration"""
        try:
            import glob
            setting_found = False
            found_in_files = []
            
            # Check each limits file
            for limits_pattern in limits_files:
                if '*' in limits_pattern:
                    # Handle wildcard patterns like /etc/security/limits.d/*
                    files_to_check = glob.glob(limits_pattern)
                else:
                    files_to_check = [limits_pattern]
                
                for limits_file in files_to_check:
                    if os.path.exists(limits_file):
                        try:
                            with open(limits_file, 'r') as f:
                                content = f.read()
                                if expected_setting in content or "* hard core 0" in content:
                                    setting_found = True
                                    found_in_files.append(limits_file)
                        except:
                            continue
            
            # Also check sysctl for fs.suid_dumpable
            stdout, stderr, returncode = self._run_command("sysctl fs.suid_dumpable")
            suid_dumpable_ok = False
            if returncode == 0 and "fs.suid_dumpable = 0" in stdout:
                suid_dumpable_ok = True
            
            if setting_found or suid_dumpable_ok:
                status = "PASS"
                current = f"Core dumps restricted in: {', '.join(found_in_files) if found_in_files else 'sysctl'}"
            else:
                status = "FAIL"
                current = "Core dump restrictions not found"
            
            return {
                "status": status,
                "current": current,
                "expected": expected_setting,
                "evidence": f"Checked files: {', '.join(limits_files)}, Found in: {', '.join(found_in_files)}"
            }
            
        except Exception as e:
            return {
                "status": "ERROR",
                "current": "Error checking core dump restrictions",
                "expected": expected_setting,
                "evidence": str(e)
            }
    
    def check_service_not_in_use(self, service_names: List[str], package_names: List[str]) -> Dict[str, Any]:
        """Check that services are not running and packages are not installed"""
        try:
            issues = []
            
            # Check if services are running
            running_services = []
            for service in service_names:
                stdout, stderr, returncode = self._run_command(f"systemctl is-active {service}")
                if returncode == 0 and stdout.strip() == "active":
                    running_services.append(service)
            
            # Check if services are enabled
            enabled_services = []
            for service in service_names:
                stdout, stderr, returncode = self._run_command(f"systemctl is-enabled {service}")
                if returncode == 0 and stdout.strip() in ["enabled", "static"]:
                    enabled_services.append(service)
            
            # Check if packages are installed
            installed_packages = []
            for package in package_names:
                stdout, stderr, returncode = self._run_command(f"dpkg -l {package}")
                if returncode == 0 and "ii" in stdout:
                    installed_packages.append(package)
                else:
                    # Try rpm for RHEL-based systems
                    stdout, stderr, returncode = self._run_command(f"rpm -q {package}")
                    if returncode == 0:
                        installed_packages.append(package)
            
            # Determine status
            if running_services:
                issues.append(f"Running services: {', '.join(running_services)}")
            if enabled_services:
                issues.append(f"Enabled services: {', '.join(enabled_services)}")
            if installed_packages:
                issues.append(f"Installed packages: {', '.join(installed_packages)}")
            
            if issues:
                status = "FAIL"
                current = "; ".join(issues)
            else:
                status = "PASS"
                current = "Services not running and packages not installed"
            
            return {
                "status": status,
                "current": current,
                "expected": "Services disabled and packages removed",
                "evidence": f"Checked services: {', '.join(service_names)}, packages: {', '.join(package_names)}"
            }
            
        except Exception as e:
            return {
                "status": "ERROR",
                "current": "Error checking services/packages",
                "expected": "Services disabled and packages removed",
                "evidence": str(e)
            }
    
    def check_mta_local_only(self, config_file: str, expected_setting: str) -> Dict[str, Any]:
        """Check Mail Transfer Agent is configured for local-only mode"""
        try:
            if not os.path.exists(config_file):
                return {
                    "status": "FAIL",
                    "current": "Config file not found",
                    "expected": expected_setting,
                    "evidence": f"MTA config file {config_file} does not exist"
                }
            
            with open(config_file, 'r') as f:
                content = f.read()
            
            # Check for inet_interfaces setting
            inet_interfaces_found = False
            current_setting = ""
            
            for line in content.split('\n'):
                line = line.strip()
                if line.startswith('inet_interfaces') and not line.startswith('#'):
                    inet_interfaces_found = True
                    current_setting = line
                    break
            
            if not inet_interfaces_found:
                status = "FAIL"
                current = "inet_interfaces not configured"
            elif "loopback-only" in current_setting or "localhost" in current_setting:
                status = "PASS"
                current = current_setting
            else:
                status = "FAIL"
                current = current_setting
            
            return {
                "status": status,
                "current": current,
                "expected": expected_setting,
                "evidence": f"In {config_file}: {current}"
            }
            
        except Exception as e:
            return {
                "status": "ERROR",
                "current": "Error checking MTA configuration",
                "expected": expected_setting,
                "evidence": str(e)
            }
    
    def check_wireless_interface(self, expected_status: str) -> Dict[str, Any]:
        """Check wireless interface status"""
        try:
            # Check if wireless interfaces exist
            stdout, stderr, returncode = self._run_command("iwconfig")
            if returncode != 0:
                # iwconfig not available, try ip command
                stdout, stderr, returncode = self._run_command("ip link show | grep -i wireless")
                if returncode != 0:
                    return {
                        "status": "PASS",
                        "current": "No wireless interfaces found",
                        "expected": f"Wireless interfaces {expected_status}",
                        "evidence": "No wireless hardware detected"
                    }
            
            # Check NetworkManager radio status
            stdout, stderr, returncode = self._run_command("nmcli radio wifi")
            wifi_enabled = False
            if returncode == 0:
                wifi_enabled = "enabled" in stdout.lower()
            
            # Check rfkill status
            stdout, stderr, returncode = self._run_command("rfkill list")
            rfkill_blocked = False
            if returncode == 0 and "Wireless LAN" in stdout:
                rfkill_blocked = "Soft blocked: yes" in stdout or "Hard blocked: yes" in stdout
            
            if expected_status == "disabled":
                if not wifi_enabled or rfkill_blocked:
                    status = "PASS"
                    current = "Wireless disabled"
                else:
                    status = "FAIL"
                    current = "Wireless enabled"
            else:
                status = "FAIL"
                current = f"Unexpected expected_status: {expected_status}"
            
            return {
                "status": status,
                "current": current,
                "expected": f"Wireless interfaces {expected_status}",
                "evidence": f"WiFi enabled: {wifi_enabled}, RF blocked: {rfkill_blocked}"
            }
            
        except Exception as e:
            return {
                "status": "ERROR",
                "current": "Error checking wireless interfaces",
                "expected": f"Wireless interfaces {expected_status}",
                "evidence": str(e)
            }
    
    def check_multi_kernel_parameters(self, parameters: List[Dict[str, str]]) -> Dict[str, Any]:
        """Check multiple kernel parameters"""
        try:
            failed_params = []
            passed_params = []
            
            for param_config in parameters:
                param_name = param_config.get('name', '')
                expected_value = param_config.get('expected_value', '')
                
                stdout, stderr, returncode = self._run_command(f"sysctl {param_name}")
                
                if returncode != 0:
                    failed_params.append(f"{param_name}: not found")
                    continue
                
                current_value = stdout.split('=')[1].strip() if '=' in stdout else stdout.strip()
                
                if current_value == expected_value:
                    passed_params.append(f"{param_name}={current_value}")
                else:
                    failed_params.append(f"{param_name}={current_value} (expected {expected_value})")
            
            if failed_params:
                status = "FAIL"
                current = f"Failed: {'; '.join(failed_params)}"
                if passed_params:
                    current += f"; Passed: {'; '.join(passed_params)}"
            else:
                status = "PASS"
                current = f"All parameters correct: {'; '.join(passed_params)}"
            
            expected_list = [f"{p.get('name')}={p.get('expected_value')}" for p in parameters]
            
            return {
                "status": status,
                "current": current,
                "expected": "; ".join(expected_list),
                "evidence": f"Checked {len(parameters)} parameters: {len(passed_params)} passed, {len(failed_params)} failed"
            }
            
        except Exception as e:
            return {
                "status": "ERROR",
                "current": "Error checking kernel parameters",
                "expected": "Multiple kernel parameters configured",
                "evidence": str(e)
            }
    
    def check_single_firewall(self, firewall_utilities: List[str]) -> Dict[str, Any]:
        """Check that only one firewall utility is active"""
        try:
            active_firewalls = []
            
            # Check ufw
            stdout, stderr, returncode = self._run_command("ufw status")
            if returncode == 0 and "Status: active" in stdout:
                active_firewalls.append("ufw")
            
            # Check nftables
            stdout, stderr, returncode = self._run_command("nft list tables")
            if returncode == 0 and stdout.strip():
                active_firewalls.append("nftables")
            
            # Check iptables
            stdout, stderr, returncode = self._run_command("iptables -L")
            if returncode == 0:
                # Check if there are non-default rules
                lines = stdout.split('\n')
                has_rules = any(line.strip() and not line.startswith('Chain') and not line.startswith('target') for line in lines)
                if has_rules:
                    active_firewalls.append("iptables")
            
            if len(active_firewalls) == 1:
                status = "PASS"
                current = f"Single firewall active: {active_firewalls[0]}"
            elif len(active_firewalls) == 0:
                status = "FAIL"
                current = "No firewall active"
            else:
                status = "FAIL"
                current = f"Multiple firewalls active: {', '.join(active_firewalls)}"
            
            return {
                "status": status,
                "current": current,
                "expected": "Single firewall utility active",
                "evidence": f"Checked utilities: {', '.join(firewall_utilities)}, Active: {', '.join(active_firewalls)}"
            }
            
        except Exception as e:
            return {
                "status": "ERROR",
                "current": "Error checking firewall utilities",
                "expected": "Single firewall utility active",
                "evidence": str(e)
            }
    
    def check_ufw_status(self, expected_status: str) -> Dict[str, Any]:
        """Check UFW firewall status"""
        try:
            stdout, stderr, returncode = self._run_command("ufw status")
            
            if returncode != 0:
                return {
                    "status": "FAIL",
                    "current": "UFW not available",
                    "expected": f"UFW {expected_status}",
                    "evidence": "UFW command failed or not installed"
                }
            
            if "Status: active" in stdout:
                current_status = "active"
            elif "Status: inactive" in stdout:
                current_status = "inactive"
            else:
                current_status = "unknown"
            
            status = "PASS" if current_status == expected_status else "FAIL"
            
            return {
                "status": status,
                "current": f"UFW {current_status}",
                "expected": f"UFW {expected_status}",
                "evidence": f"UFW status: {current_status}"
            }
            
        except Exception as e:
            return {
                "status": "ERROR",
                "current": "Error checking UFW status",
                "expected": f"UFW {expected_status}",
                "evidence": str(e)
            }
    
    def check_ufw_loopback(self, expected_rules: List[str]) -> Dict[str, Any]:
        """Check UFW loopback configuration"""
        try:
            stdout, stderr, returncode = self._run_command("ufw status numbered")
            
            if returncode != 0:
                return {
                    "status": "FAIL",
                    "current": "UFW not available",
                    "expected": f"Loopback rules: {', '.join(expected_rules)}",
                    "evidence": "UFW command failed"
                }
            
            found_rules = []
            missing_rules = []
            
            for expected_rule in expected_rules:
                if expected_rule in stdout:
                    found_rules.append(expected_rule)
                else:
                    missing_rules.append(expected_rule)
            
            if not missing_rules:
                status = "PASS"
                current = f"All loopback rules configured: {', '.join(found_rules)}"
            else:
                status = "FAIL"
                current = f"Missing rules: {', '.join(missing_rules)}"
            
            return {
                "status": status,
                "current": current,
                "expected": f"Loopback rules: {', '.join(expected_rules)}",
                "evidence": f"Found: {len(found_rules)}, Missing: {len(missing_rules)}"
            }
            
        except Exception as e:
            return {
                "status": "ERROR",
                "current": "Error checking UFW loopback rules",
                "expected": f"Loopback rules: {', '.join(expected_rules)}",
                "evidence": str(e)
            }
    
    def check_ufw_open_ports(self, check_open_ports: bool) -> Dict[str, Any]:
        """Check UFW rules for open ports"""
        try:
            # Get listening ports
            stdout, stderr, returncode = self._run_command("ss -tuln")
            if returncode != 0:
                return {
                    "status": "ERROR",
                    "current": "Cannot check listening ports",
                    "expected": "UFW rules exist for all open ports",
                    "evidence": "ss command failed"
                }
            
            # Parse listening ports (simplified)
            listening_ports = []
            for line in stdout.split('\n'):
                if ':' in line and ('LISTEN' in line or 'UNCONN' in line):
                    parts = line.split()
                    if len(parts) >= 5:
                        addr_port = parts[4]
                        if ':' in addr_port:
                            port = addr_port.split(':')[-1]
                            if port.isdigit() and port not in ['22', '53']:  # Skip common system ports
                                listening_ports.append(port)
            
            # Get UFW rules
            stdout, stderr, returncode = self._run_command("ufw status numbered")
            if returncode != 0:
                return {
                    "status": "FAIL",
                    "current": "UFW not available",
                    "expected": "UFW rules exist for all open ports",
                    "evidence": "UFW command failed"
                }
            
            # This is a simplified check - in practice, this would need more sophisticated port/rule matching
            if not listening_ports:
                status = "PASS"
                current = "No additional open ports found"
            else:
                status = "MANUAL"
                current = f"Open ports detected: {', '.join(listening_ports)} - manual verification required"
            
            return {
                "status": status,
                "current": current,
                "expected": "UFW rules exist for all open ports",
                "evidence": f"Listening ports: {', '.join(listening_ports)}"
            }
            
        except Exception as e:
            return {
                "status": "ERROR",
                "current": "Error checking UFW open ports",
                "expected": "UFW rules exist for all open ports",
                "evidence": str(e)
            }
    
    def check_ufw_default_policy(self, expected_policies: Dict[str, str]) -> Dict[str, Any]:
        """Check UFW default policies"""
        try:
            stdout, stderr, returncode = self._run_command("ufw status verbose")
            
            if returncode != 0:
                return {
                    "status": "FAIL",
                    "current": "UFW not available",
                    "expected": f"Default policies: {expected_policies}",
                    "evidence": "UFW command failed"
                }
            
            current_policies = {}
            failed_policies = []
            
            for line in stdout.split('\n'):
                if 'Default:' in line:
                    # Parse default policy line
                    if 'incoming' in line:
                        policy = line.split('incoming')[1].split(',')[0].strip()
                        current_policies['incoming'] = policy
                    if 'outgoing' in line:
                        policy = line.split('outgoing')[1].split(',')[0].strip()
                        current_policies['outgoing'] = policy
                    if 'routed' in line:
                        policy = line.split('routed')[1].strip()
                        current_policies['routed'] = policy
            
            for policy_type, expected_value in expected_policies.items():
                current_value = current_policies.get(policy_type, 'unknown')
                if current_value != expected_value:
                    failed_policies.append(f"{policy_type}: {current_value} (expected {expected_value})")
            
            if not failed_policies:
                status = "PASS"
                current = f"All default policies correct: {current_policies}"
            else:
                status = "FAIL"
                current = f"Policy issues: {'; '.join(failed_policies)}"
            
            return {
                "status": status,
                "current": current,
                "expected": f"Default policies: {expected_policies}",
                "evidence": f"Current policies: {current_policies}"
            }
            
        except Exception as e:
            return {
                "status": "ERROR",
                "current": "Error checking UFW default policies",
                "expected": f"Default policies: {expected_policies}",
                "evidence": str(e)
            }
    
    def check_nftables_table(self, expected_families: List[str]) -> Dict[str, Any]:
        """Check nftables table existence"""
        try:
            stdout, stderr, returncode = self._run_command("nft list tables")
            
            if returncode != 0:
                return {
                    "status": "FAIL",
                    "current": "nftables not available",
                    "expected": f"Tables with families: {', '.join(expected_families)}",
                    "evidence": "nft command failed or not installed"
                }
            
            if not stdout.strip():
                return {
                    "status": "FAIL",
                    "current": "No nftables tables found",
                    "expected": f"Tables with families: {', '.join(expected_families)}",
                    "evidence": "No tables configured"
                }
            
            found_families = []
            for line in stdout.split('\n'):
                if 'table' in line:
                    parts = line.split()
                    if len(parts) >= 3:
                        family = parts[1]
                        if family in expected_families:
                            found_families.append(family)
            
            if found_families:
                status = "PASS"
                current = f"Tables found with families: {', '.join(set(found_families))}"
            else:
                status = "FAIL"
                current = "No tables with expected families found"
            
            return {
                "status": status,
                "current": current,
                "expected": f"Tables with families: {', '.join(expected_families)}",
                "evidence": f"Found families: {', '.join(set(found_families))}"
            }
            
        except Exception as e:
            return {
                "status": "ERROR",
                "current": "Error checking nftables tables",
                "expected": f"Tables with families: {', '.join(expected_families)}",
                "evidence": str(e)
            }
    
    def check_nftables_base_chains(self, required_hooks: List[str]) -> Dict[str, Any]:
        """Check nftables base chains"""
        try:
            stdout, stderr, returncode = self._run_command("nft list ruleset")
            
            if returncode != 0:
                return {
                    "status": "FAIL",
                    "current": "nftables not available",
                    "expected": f"Base chains with hooks: {', '.join(required_hooks)}",
                    "evidence": "nft command failed"
                }
            
            found_hooks = []
            for line in stdout.split('\n'):
                if 'hook' in line:
                    for hook in required_hooks:
                        if f'hook {hook}' in line:
                            found_hooks.append(hook)
            
            missing_hooks = [hook for hook in required_hooks if hook not in found_hooks]
            
            if not missing_hooks:
                status = "PASS"
                current = f"All required base chains found: {', '.join(set(found_hooks))}"
            else:
                status = "FAIL"
                current = f"Missing base chains: {', '.join(missing_hooks)}"
            
            return {
                "status": status,
                "current": current,
                "expected": f"Base chains with hooks: {', '.join(required_hooks)}",
                "evidence": f"Found hooks: {', '.join(set(found_hooks))}, Missing: {', '.join(missing_hooks)}"
            }
            
        except Exception as e:
            return {
                "status": "ERROR",
                "current": "Error checking nftables base chains",
                "expected": f"Base chains with hooks: {', '.join(required_hooks)}",
                "evidence": str(e)
            }
    
    def check_ssh_private_keys(self, key_pattern: str, expected_mode: str, expected_owner: str, expected_group: str) -> Dict[str, Any]:
        """Check SSH private key file permissions"""
        try:
            import glob
            key_files = glob.glob(key_pattern)
            
            if not key_files:
                return {
                    "status": "PASS",
                    "current": "No SSH private keys found",
                    "expected": f"SSH private keys with mode {expected_mode}, owner {expected_owner}, group {expected_group}",
                    "evidence": f"No files matching pattern {key_pattern}"
                }
            
            failed_files = []
            passed_files = []
            
            for key_file in key_files:
                result = self.check_file_permissions(key_file, expected_mode, expected_owner, expected_group)
                if result['status'] == 'PASS':
                    passed_files.append(key_file)
                else:
                    failed_files.append(f"{key_file}: {result['current']}")
            
            if not failed_files:
                status = "PASS"
                current = f"All SSH private keys properly secured: {len(passed_files)} files"
            else:
                status = "FAIL"
                current = f"Issues with {len(failed_files)} files: {'; '.join(failed_files)}"
            
            return {
                "status": status,
                "current": current,
                "expected": f"SSH private keys with mode {expected_mode}, owner {expected_owner}, group {expected_group}",
                "evidence": f"Checked {len(key_files)} private key files"
            }
            
        except Exception as e:
            return {
                "status": "ERROR",
                "current": "Error checking SSH private keys",
                "expected": f"SSH private keys with mode {expected_mode}, owner {expected_owner}, group {expected_group}",
                "evidence": str(e)
            }
    
    def check_ssh_public_keys(self, key_pattern: str, expected_mode: str, expected_owner: str, expected_group: str) -> Dict[str, Any]:
        """Check SSH public key file permissions"""
        try:
            import glob
            key_files = glob.glob(key_pattern)
            
            if not key_files:
                return {
                    "status": "PASS",
                    "current": "No SSH public keys found",
                    "expected": f"SSH public keys with mode {expected_mode}, owner {expected_owner}, group {expected_group}",
                    "evidence": f"No files matching pattern {key_pattern}"
                }
            
            failed_files = []
            passed_files = []
            
            for key_file in key_files:
                result = self.check_file_permissions(key_file, expected_mode, expected_owner, expected_group)
                if result['status'] == 'PASS':
                    passed_files.append(key_file)
                else:
                    failed_files.append(f"{key_file}: {result['current']}")
            
            if not failed_files:
                status = "PASS"
                current = f"All SSH public keys properly configured: {len(passed_files)} files"
            else:
                status = "FAIL"
                current = f"Issues with {len(failed_files)} files: {'; '.join(failed_files)}"
            
            return {
                "status": status,
                "current": current,
                "expected": f"SSH public keys with mode {expected_mode}, owner {expected_owner}, group {expected_group}",
                "evidence": f"Checked {len(key_files)} public key files"
            }
            
        except Exception as e:
            return {
                "status": "ERROR",
                "current": "Error checking SSH public keys",
                "expected": f"SSH public keys with mode {expected_mode}, owner {expected_owner}, group {expected_group}",
                "evidence": str(e)
            }
    
    def check_sshd_config(self, config_file: str, check_parameters: List[str], expected_values: Dict[str, str], require_one_of: bool, validate_crypto: bool) -> Dict[str, Any]:
        """Check SSH daemon configuration"""
        try:
            if not os.path.exists(config_file):
                return {
                    "status": "FAIL",
                    "current": "SSH config file not found",
                    "expected": f"Parameters configured: {', '.join(check_parameters)}",
                    "evidence": f"Config file {config_file} does not exist"
                }
            
            with open(config_file, 'r') as f:
                content = f.read()
            
            found_params = {}
            issues = []
            
            for line in content.split('\n'):
                line = line.strip()
                if line and not line.startswith('#'):
                    for param in check_parameters:
                        if line.lower().startswith(param.lower()):
                            value = line.split(None, 1)[1] if len(line.split(None, 1)) > 1 else ""
                            found_params[param] = value
            
            if require_one_of:
                # At least one parameter must be configured
                if not found_params:
                    status = "FAIL"
                    current = "No access control parameters configured"
                else:
                    status = "PASS"
                    current = f"Access control configured: {', '.join(f'{k}={v}' for k, v in found_params.items())}"
            else:
                # Check specific expected values
                for param, expected_value in expected_values.items():
                    current_value = found_params.get(param, 'not set')
                    if current_value != expected_value:
                        issues.append(f"{param}: {current_value} (expected {expected_value})")
                
                if not issues:
                    status = "PASS"
                    current = f"All parameters correctly configured: {', '.join(f'{k}={v}' for k, v in found_params.items())}"
                else:
                    status = "FAIL"
                    current = f"Configuration issues: {'; '.join(issues)}"
            
            return {
                "status": status,
                "current": current,
                "expected": f"Parameters configured: {', '.join(check_parameters)}",
                "evidence": f"Found parameters: {', '.join(f'{k}={v}' for k, v in found_params.items())}"
            }
            
        except Exception as e:
            return {
                "status": "ERROR",
                "current": "Error checking SSH configuration",
                "expected": f"Parameters configured: {', '.join(check_parameters)}",
                "evidence": str(e)
            }
    
    def check_sudo_config(self, config_files: List[str], required_setting: str, prohibited_setting: str) -> Dict[str, Any]:
        """Check sudo configuration"""
        try:
            import glob
            all_files = []
            
            for config_pattern in config_files:
                if '*' in config_pattern:
                    all_files.extend(glob.glob(config_pattern))
                else:
                    if os.path.exists(config_pattern):
                        all_files.append(config_pattern)
            
            if not all_files:
                return {
                    "status": "FAIL",
                    "current": "No sudo config files found",
                    "expected": f"Required: {required_setting}, Prohibited: {prohibited_setting}",
                    "evidence": "No sudo configuration files exist"
                }
            
            found_required = False
            found_prohibited = []
            
            for config_file in all_files:
                try:
                    with open(config_file, 'r') as f:
                        content = f.read()
                    
                    if required_setting and required_setting in content:
                        found_required = True
                    
                    if prohibited_setting:
                        for line in content.split('\n'):
                            line = line.strip()
                            if line and not line.startswith('#') and prohibited_setting in line:
                                found_prohibited.append(f"{config_file}: {line}")
                except:
                    continue
            
            issues = []
            if required_setting and not found_required:
                issues.append(f"Missing required setting: {required_setting}")
            if prohibited_setting and found_prohibited:
                issues.append(f"Found prohibited setting: {'; '.join(found_prohibited)}")
            
            if not issues:
                status = "PASS"
                current = "Sudo configuration compliant"
            else:
                status = "FAIL"
                current = "; ".join(issues)
            
            return {
                "status": status,
                "current": current,
                "expected": f"Required: {required_setting}, Prohibited: {prohibited_setting}",
                "evidence": f"Checked {len(all_files)} sudo config files"
            }
            
        except Exception as e:
            return {
                "status": "ERROR",
                "current": "Error checking sudo configuration",
                "expected": f"Required: {required_setting}, Prohibited: {prohibited_setting}",
                "evidence": str(e)
            }
    
    def check_pam_config(self, config_file: str, required_setting: str) -> Dict[str, Any]:
        """Check PAM configuration"""
        try:
            if not os.path.exists(config_file):
                return {
                    "status": "FAIL",
                    "current": "PAM config file not found",
                    "expected": required_setting,
                    "evidence": f"Config file {config_file} does not exist"
                }
            
            with open(config_file, 'r') as f:
                content = f.read()
            
            if required_setting in content:
                status = "PASS"
                current = "Required PAM setting found"
            else:
                status = "FAIL"
                current = "Required PAM setting not found"
            
            return {
                "status": status,
                "current": current,
                "expected": required_setting,
                "evidence": f"Checked PAM config file: {config_file}"
            }
            
        except Exception as e:
            return {
                "status": "ERROR",
                "current": "Error checking PAM configuration",
                "expected": required_setting,
                "evidence": str(e)
            }
    
    def check_single_logging_system(self, logging_services: List[str]) -> Dict[str, Any]:
        """Check that only one logging system is active"""
        try:
            active_services = []
            
            for service in logging_services:
                stdout, stderr, returncode = self._run_command(f"systemctl is-active {service}")
                if returncode == 0 and stdout.strip() == "active":
                    active_services.append(service)
            
            if len(active_services) == 1:
                status = "PASS"
                current = f"Single logging system active: {active_services[0]}"
            elif len(active_services) == 0:
                status = "FAIL"
                current = "No logging system active"
            else:
                status = "FAIL"
                current = f"Multiple logging systems active: {', '.join(active_services)}"
            
            return {
                "status": status,
                "current": current,
                "expected": "Single logging system active",
                "evidence": f"Checked services: {', '.join(logging_services)}, Active: {', '.join(active_services)}"
            }
            
        except Exception as e:
            return {
                "status": "ERROR",
                "current": "Error checking logging systems",
                "expected": "Single logging system active",
                "evidence": str(e)
            }
    
    def check_journald_config(self, config_file: str, parameter: str, expected_value: str) -> Dict[str, Any]:
        """Check systemd-journald configuration"""
        try:
            if not os.path.exists(config_file):
                return {
                    "status": "FAIL",
                    "current": "Journald config file not found",
                    "expected": f"{parameter}={expected_value}",
                    "evidence": f"Config file {config_file} does not exist"
                }
            
            with open(config_file, 'r') as f:
                content = f.read()
            
            current_value = None
            for line in content.split('\n'):
                line = line.strip()
                if line.startswith(f"{parameter}=") and not line.startswith('#'):
                    current_value = line.split('=', 1)[1]
                    break
            
            if current_value == expected_value:
                status = "PASS"
                current = f"{parameter}={current_value}"
            elif current_value is None:
                status = "FAIL"
                current = f"{parameter} not configured"
            else:
                status = "FAIL"
                current = f"{parameter}={current_value} (expected {expected_value})"
            
            return {
                "status": status,
                "current": current,
                "expected": f"{parameter}={expected_value}",
                "evidence": f"In {config_file}: {current}"
            }
            
        except Exception as e:
            return {
                "status": "ERROR",
                "current": "Error checking journald configuration",
                "expected": f"{parameter}={expected_value}",
                "evidence": str(e)
            }
    
    def check_rsyslog_config(self, config_files: List[str], prohibited_directives: List[str]) -> Dict[str, Any]:
        """Check rsyslog configuration for prohibited directives"""
        try:
            import glob
            all_files = []
            
            for config_pattern in config_files:
                if '*' in config_pattern:
                    all_files.extend(glob.glob(config_pattern))
                else:
                    if os.path.exists(config_pattern):
                        all_files.append(config_pattern)
            
            found_prohibited = []
            
            for config_file in all_files:
                try:
                    with open(config_file, 'r') as f:
                        content = f.read()
                    
                    for line in content.split('\n'):
                        line = line.strip()
                        if line and not line.startswith('#'):
                            for directive in prohibited_directives:
                                if directive in line:
                                    found_prohibited.append(f"{config_file}: {line}")
                except:
                    continue
            
            if not found_prohibited:
                status = "PASS"
                current = "No prohibited directives found"
            else:
                status = "FAIL"
                current = f"Found prohibited directives: {'; '.join(found_prohibited)}"
            
            return {
                "status": status,
                "current": current,
                "expected": f"No prohibited directives: {', '.join(prohibited_directives)}",
                "evidence": f"Checked {len(all_files)} rsyslog config files"
            }
            
        except Exception as e:
            return {
                "status": "ERROR",
                "current": "Error checking rsyslog configuration",
                "expected": f"No prohibited directives: {', '.join(prohibited_directives)}",
                "evidence": str(e)
            }
    
    def check_log_file_permissions(self, log_directory: str, expected_file_permissions: str, expected_dir_permissions: str) -> Dict[str, Any]:
        """Check log file and directory permissions"""
        try:
            if not os.path.exists(log_directory):
                return {
                    "status": "FAIL",
                    "current": "Log directory not found",
                    "expected": f"Files: {expected_file_permissions}, Dirs: {expected_dir_permissions}",
                    "evidence": f"Directory {log_directory} does not exist"
                }
            
            issues = []
            checked_files = 0
            checked_dirs = 0
            
            for root, dirs, files in os.walk(log_directory):
                # Check directory permissions
                for d in dirs:
                    dir_path = os.path.join(root, d)
                    try:
                        dir_stat = os.stat(dir_path)
                        current_mode = oct(dir_stat.st_mode)[-3:]
                        if current_mode > expected_dir_permissions:
                            issues.append(f"Dir {dir_path}: {current_mode}")
                        checked_dirs += 1
                    except:
                        continue
                
                # Check file permissions
                for f in files:
                    file_path = os.path.join(root, f)
                    try:
                        file_stat = os.stat(file_path)
                        current_mode = oct(file_stat.st_mode)[-3:]
                        if current_mode > expected_file_permissions:
                            issues.append(f"File {file_path}: {current_mode}")
                        checked_files += 1
                    except:
                        continue
            
            if not issues:
                status = "PASS"
                current = f"All permissions correct: {checked_files} files, {checked_dirs} dirs"
            else:
                status = "FAIL"
                current = f"Permission issues: {'; '.join(issues[:5])}{'...' if len(issues) > 5 else ''}"
            
            return {
                "status": status,
                "current": current,
                "expected": f"Files: {expected_file_permissions}, Dirs: {expected_dir_permissions}",
                "evidence": f"Checked {checked_files} files, {checked_dirs} directories"
            }
            
        except Exception as e:
            return {
                "status": "ERROR",
                "current": "Error checking log file permissions",
                "expected": f"Files: {expected_file_permissions}, Dirs: {expected_dir_permissions}",
                "evidence": str(e)
            }
    
    def check_multi_packages(self, package_names: List[str], should_be_installed: bool) -> Dict[str, Any]:
        """Check multiple packages installation status"""
        try:
            missing_packages = []
            installed_packages = []
            
            for package in package_names:
                stdout, stderr, returncode = self._run_command(f"dpkg -l {package}")
                if returncode == 0 and "ii" in stdout:
                    installed_packages.append(package)
                else:
                    # Try rpm for RHEL-based systems
                    stdout, stderr, returncode = self._run_command(f"rpm -q {package}")
                    if returncode == 0:
                        installed_packages.append(package)
                    else:
                        missing_packages.append(package)
            
            if should_be_installed:
                if not missing_packages:
                    status = "PASS"
                    current = f"All packages installed: {', '.join(installed_packages)}"
                else:
                    status = "FAIL"
                    current = f"Missing packages: {', '.join(missing_packages)}"
            else:
                if not installed_packages:
                    status = "PASS"
                    current = "No packages installed"
                else:
                    status = "FAIL"
                    current = f"Packages still installed: {', '.join(installed_packages)}"
            
            return {
                "status": status,
                "current": current,
                "expected": f"Packages {'installed' if should_be_installed else 'not installed'}: {', '.join(package_names)}",
                "evidence": f"Checked {len(package_names)} packages"
            }
            
        except Exception as e:
            return {
                "status": "ERROR",
                "current": "Error checking packages",
                "expected": f"Packages {'installed' if should_be_installed else 'not installed'}: {', '.join(package_names)}",
                "evidence": str(e)
            }
    
    def check_auditd_config(self, config_file: str, parameter: str, expected_value: str, check_configured: bool) -> Dict[str, Any]:
        """Check auditd configuration"""
        try:
            if not os.path.exists(config_file):
                return {
                    "status": "FAIL",
                    "current": "Auditd config file not found",
                    "expected": f"{parameter}={expected_value}" if expected_value else f"{parameter} configured",
                    "evidence": f"Config file {config_file} does not exist"
                }
            
            with open(config_file, 'r') as f:
                content = f.read()
            
            current_value = None
            for line in content.split('\n'):
                line = line.strip()
                if line.startswith(f"{parameter} =") and not line.startswith('#'):
                    current_value = line.split('=', 1)[1].strip()
                    break
            
            if check_configured:
                # Just check if parameter is configured
                if current_value is not None:
                    status = "PASS"
                    current = f"{parameter}={current_value}"
                else:
                    status = "FAIL"
                    current = f"{parameter} not configured"
            else:
                # Check specific value
                if current_value == expected_value:
                    status = "PASS"
                    current = f"{parameter}={current_value}"
                elif current_value is None:
                    status = "FAIL"
                    current = f"{parameter} not configured"
                else:
                    status = "FAIL"
                    current = f"{parameter}={current_value} (expected {expected_value})"
            
            return {
                "status": status,
                "current": current,
                "expected": f"{parameter}={expected_value}" if expected_value else f"{parameter} configured",
                "evidence": f"In {config_file}: {current}"
            }
            
        except Exception as e:
            return {
                "status": "ERROR",
                "current": "Error checking auditd configuration",
                "expected": f"{parameter}={expected_value}" if expected_value else f"{parameter} configured",
                "evidence": str(e)
            }
    
    def check_audit_rule(self, rule_file: str, expected_rules: List[str]) -> Dict[str, Any]:
        """Check audit rules configuration"""
        try:
            if not os.path.exists(rule_file):
                return {
                    "status": "FAIL",
                    "current": "Audit rule file not found",
                    "expected": f"Rules: {', '.join(expected_rules)}",
                    "evidence": f"Rule file {rule_file} does not exist"
                }
            
            with open(rule_file, 'r') as f:
                content = f.read()
            
            missing_rules = []
            found_rules = []
            
            for expected_rule in expected_rules:
                if expected_rule in content:
                    found_rules.append(expected_rule)
                else:
                    missing_rules.append(expected_rule)
            
            if not missing_rules:
                status = "PASS"
                current = f"All audit rules configured: {len(found_rules)} rules"
            else:
                status = "FAIL"
                current = f"Missing rules: {len(missing_rules)}, Found: {len(found_rules)}"
            
            return {
                "status": status,
                "current": current,
                "expected": f"Rules: {', '.join(expected_rules)}",
                "evidence": f"Rule file: {rule_file}, Found: {len(found_rules)}, Missing: {len(missing_rules)}"
            }
            
        except Exception as e:
            return {
                "status": "ERROR",
                "current": "Error checking audit rules",
                "expected": f"Rules: {', '.join(expected_rules)}",
                "evidence": str(e)
            }
    
    def check_audit_log_permissions(self, log_directory: str, expected_file_mode: str, expected_owner: str, expected_group: str) -> Dict[str, Any]:
        """Check audit log file permissions"""
        try:
            if not os.path.exists(log_directory):
                return {
                    "status": "FAIL",
                    "current": "Audit log directory not found",
                    "expected": f"Mode: {expected_file_mode}, Owner: {expected_owner}, Group: {expected_group}",
                    "evidence": f"Directory {log_directory} does not exist"
                }
            
            issues = []
            checked_files = 0
            
            for file_name in os.listdir(log_directory):
                file_path = os.path.join(log_directory, file_name)
                if os.path.isfile(file_path):
                    result = self.check_file_permissions(file_path, expected_file_mode, expected_owner, expected_group)
                    if result['status'] != 'PASS':
                        issues.append(f"{file_name}: {result['current']}")
                    checked_files += 1
            
            if not issues:
                status = "PASS"
                current = f"All audit log files properly secured: {checked_files} files"
            else:
                status = "FAIL"
                current = f"Permission issues: {'; '.join(issues[:3])}{'...' if len(issues) > 3 else ''}"
            
            return {
                "status": status,
                "current": current,
                "expected": f"Mode: {expected_file_mode}, Owner: {expected_owner}, Group: {expected_group}",
                "evidence": f"Checked {checked_files} audit log files"
            }
            
        except Exception as e:
            return {
                "status": "ERROR",
                "current": "Error checking audit log permissions",
                "expected": f"Mode: {expected_file_mode}, Owner: {expected_owner}, Group: {expected_group}",
                "evidence": str(e)
            }
    
    def check_cron_job(self, cron_user: str, expected_job: str, job_description: str) -> Dict[str, Any]:
        """Check cron job configuration"""
        try:
            stdout, stderr, returncode = self._run_command(f"crontab -u {cron_user} -l")
            
            if returncode != 0:
                return {
                    "status": "FAIL",
                    "current": f"No crontab for user {cron_user}",
                    "expected": f"Cron job containing: {expected_job}",
                    "evidence": f"crontab -u {cron_user} -l failed"
                }
            
            if expected_job in stdout:
                status = "PASS"
                current = f"Cron job found for {job_description}"
            else:
                status = "FAIL"
                current = f"Cron job not found for {job_description}"
            
            return {
                "status": status,
                "current": current,
                "expected": f"Cron job containing: {expected_job}",
                "evidence": f"Checked crontab for user {cron_user}"
            }
            
        except Exception as e:
            return {
                "status": "ERROR",
                "current": "Error checking cron job",
                "expected": f"Cron job containing: {expected_job}",
                "evidence": str(e)
            }
    
    def check_aide_config(self, config_file: str, monitored_tools: List[str]) -> Dict[str, Any]:
        """Check AIDE configuration for monitored tools"""
        try:
            if not os.path.exists(config_file):
                return {
                    "status": "FAIL",
                    "current": "AIDE config file not found",
                    "expected": f"Monitoring tools: {', '.join(monitored_tools)}",
                    "evidence": f"Config file {config_file} does not exist"
                }
            
            with open(config_file, 'r') as f:
                content = f.read()
            
            missing_tools = []
            found_tools = []
            
            for tool in monitored_tools:
                if tool in content:
                    found_tools.append(tool)
                else:
                    missing_tools.append(tool)
            
            if not missing_tools:
                status = "PASS"
                current = f"All audit tools monitored: {len(found_tools)} tools"
            else:
                status = "FAIL"
                current = f"Missing tools: {len(missing_tools)}, Found: {len(found_tools)}"
            
            return {
                "status": status,
                "current": current,
                "expected": f"Monitoring tools: {', '.join(monitored_tools)}",
                "evidence": f"AIDE config: {config_file}, Found: {len(found_tools)}, Missing: {len(missing_tools)}"
            }
            
        except Exception as e:
            return {
                "status": "ERROR",
                "current": "Error checking AIDE configuration",
                "expected": f"Monitoring tools: {', '.join(monitored_tools)}",
                "evidence": str(e)
            }
    
    def check_world_writable_files(self, search_paths: List[str], exclude_paths: List[str]) -> Dict[str, Any]:
        """Check for world-writable files and directories"""
        try:
            world_writable = []
            
            for search_path in search_paths:
                if not os.path.exists(search_path):
                    continue
                
                # Use find command for efficiency
                exclude_args = ' '.join([f"-path {path} -prune -o" for path in exclude_paths])
                find_cmd = f"find {search_path} {exclude_args} -type f -perm -0002 -print 2>/dev/null | head -20"
                
                stdout, stderr, returncode = self._run_command(find_cmd)
                if returncode == 0 and stdout.strip():
                    world_writable.extend(stdout.strip().split('\n'))
            
            if not world_writable:
                status = "PASS"
                current = "No world-writable files found"
            else:
                status = "FAIL"
                current = f"Found {len(world_writable)} world-writable files: {', '.join(world_writable[:5])}{'...' if len(world_writable) > 5 else ''}"
            
            return {
                "status": status,
                "current": current,
                "expected": "No world-writable files",
                "evidence": f"Searched paths: {', '.join(search_paths)}, Found: {len(world_writable)} files"
            }
            
        except Exception as e:
            return {
                "status": "ERROR",
                "current": "Error checking world-writable files",
                "expected": "No world-writable files",
                "evidence": str(e)
            }
    
    def check_orphaned_files(self, search_paths: List[str], exclude_paths: List[str]) -> Dict[str, Any]:
        """Check for files without valid owner or group"""
        try:
            orphaned_files = []
            
            for search_path in search_paths:
                if not os.path.exists(search_path):
                    continue
                
                # Use find command to locate orphaned files
                exclude_args = ' '.join([f"-path {path} -prune -o" for path in exclude_paths])
                find_cmd = f"find {search_path} {exclude_args} -nouser -o -nogroup -print 2>/dev/null | head -20"
                
                stdout, stderr, returncode = self._run_command(find_cmd)
                if returncode == 0 and stdout.strip():
                    orphaned_files.extend(stdout.strip().split('\n'))
            
            if not orphaned_files:
                status = "PASS"
                current = "No orphaned files found"
            else:
                status = "FAIL"
                current = f"Found {len(orphaned_files)} orphaned files: {', '.join(orphaned_files[:5])}{'...' if len(orphaned_files) > 5 else ''}"
            
            return {
                "status": status,
                "current": current,
                "expected": "No orphaned files",
                "evidence": f"Searched paths: {', '.join(search_paths)}, Found: {len(orphaned_files)} files"
            }
            
        except Exception as e:
            return {
                "status": "ERROR",
                "current": "Error checking orphaned files",
                "expected": "No orphaned files",
                "evidence": str(e)
            }
    
    def check_shadowed_passwords(self, passwd_file: str) -> Dict[str, Any]:
        """Check that all accounts use shadowed passwords"""
        try:
            if not os.path.exists(passwd_file):
                return {
                    "status": "FAIL",
                    "current": "passwd file not found",
                    "expected": "All accounts use shadowed passwords",
                    "evidence": f"File {passwd_file} does not exist"
                }
            
            non_shadowed = []
            
            with open(passwd_file, 'r') as f:
                for line in f:
                    if line.strip() and not line.startswith('#'):
                        fields = line.strip().split(':')
                        if len(fields) >= 2 and fields[1] != 'x':
                            non_shadowed.append(fields[0])
            
            if not non_shadowed:
                status = "PASS"
                current = "All accounts use shadowed passwords"
            else:
                status = "FAIL"
                current = f"Accounts not using shadowed passwords: {', '.join(non_shadowed)}"
            
            return {
                "status": status,
                "current": current,
                "expected": "All accounts use shadowed passwords",
                "evidence": f"Checked {passwd_file}, Non-shadowed: {len(non_shadowed)}"
            }
            
        except Exception as e:
            return {
                "status": "ERROR",
                "current": "Error checking shadowed passwords",
                "expected": "All accounts use shadowed passwords",
                "evidence": str(e)
            }
    
    def check_empty_passwords(self, shadow_file: str) -> Dict[str, Any]:
        """Check for accounts with empty passwords"""
        try:
            if not os.path.exists(shadow_file):
                return {
                    "status": "FAIL",
                    "current": "shadow file not found",
                    "expected": "No accounts with empty passwords",
                    "evidence": f"File {shadow_file} does not exist"
                }
            
            empty_passwords = []
            
            with open(shadow_file, 'r') as f:
                for line in f:
                    if line.strip() and not line.startswith('#'):
                        fields = line.strip().split(':')
                        if len(fields) >= 2 and fields[1] == '':
                            empty_passwords.append(fields[0])
            
            if not empty_passwords:
                status = "PASS"
                current = "No accounts with empty passwords"
            else:
                status = "FAIL"
                current = f"Accounts with empty passwords: {', '.join(empty_passwords)}"
            
            return {
                "status": status,
                "current": current,
                "expected": "No accounts with empty passwords",
                "evidence": f"Checked {shadow_file}, Empty passwords: {len(empty_passwords)}"
            }
            
        except Exception as e:
            return {
                "status": "ERROR",
                "current": "Error checking empty passwords",
                "expected": "No accounts with empty passwords",
                "evidence": str(e)
            }
    
    def check_group_consistency(self, passwd_file: str, group_file: str) -> Dict[str, Any]:
        """Check that all groups in passwd exist in group file"""
        try:
            if not os.path.exists(passwd_file) or not os.path.exists(group_file):
                return {
                    "status": "FAIL",
                    "current": "Required files not found",
                    "expected": "All passwd groups exist in group file",
                    "evidence": f"Missing files: passwd={os.path.exists(passwd_file)}, group={os.path.exists(group_file)}"
                }
            
            # Get all GIDs from passwd
            passwd_gids = set()
            with open(passwd_file, 'r') as f:
                for line in f:
                    if line.strip() and not line.startswith('#'):
                        fields = line.strip().split(':')
                        if len(fields) >= 4:
                            passwd_gids.add(fields[3])
            
            # Get all GIDs from group
            group_gids = set()
            with open(group_file, 'r') as f:
                for line in f:
                    if line.strip() and not line.startswith('#'):
                        fields = line.strip().split(':')
                        if len(fields) >= 3:
                            group_gids.add(fields[2])
            
            missing_gids = passwd_gids - group_gids
            
            if not missing_gids:
                status = "PASS"
                current = "All passwd groups exist in group file"
            else:
                status = "FAIL"
                current = f"Missing GIDs in group file: {', '.join(missing_gids)}"
            
            return {
                "status": status,
                "current": current,
                "expected": "All passwd groups exist in group file",
                "evidence": f"Passwd GIDs: {len(passwd_gids)}, Group GIDs: {len(group_gids)}, Missing: {len(missing_gids)}"
            }
            
        except Exception as e:
            return {
                "status": "ERROR",
                "current": "Error checking group consistency",
                "expected": "All passwd groups exist in group file",
                "evidence": str(e)
            }
    
    def check_empty_group(self, group_name: str, group_file: str) -> Dict[str, Any]:
        """Check that specified group has no members"""
        try:
            if not os.path.exists(group_file):
                return {
                    "status": "FAIL",
                    "current": "Group file not found",
                    "expected": f"Group {group_name} is empty",
                    "evidence": f"File {group_file} does not exist"
                }
            
            group_members = []
            
            with open(group_file, 'r') as f:
                for line in f:
                    if line.strip() and not line.startswith('#'):
                        fields = line.strip().split(':')
                        if len(fields) >= 4 and fields[0] == group_name:
                            if fields[3]:  # Group members field
                                group_members = [m.strip() for m in fields[3].split(',') if m.strip()]
                            break
            
            if not group_members:
                status = "PASS"
                current = f"Group {group_name} is empty"
            else:
                status = "FAIL"
                current = f"Group {group_name} has members: {', '.join(group_members)}"
            
            return {
                "status": status,
                "current": current,
                "expected": f"Group {group_name} is empty",
                "evidence": f"Checked group {group_name}, Members: {len(group_members)}"
            }
            
        except Exception as e:
            return {
                "status": "ERROR",
                "current": "Error checking group membership",
                "expected": f"Group {group_name} is empty",
                "evidence": str(e)
            }
    
    def check_duplicate_uids(self, passwd_file: str) -> Dict[str, Any]:
        """Check for duplicate UIDs"""
        try:
            if not os.path.exists(passwd_file):
                return {
                    "status": "FAIL",
                    "current": "passwd file not found",
                    "expected": "No duplicate UIDs",
                    "evidence": f"File {passwd_file} does not exist"
                }
            
            uid_counts = {}
            
            with open(passwd_file, 'r') as f:
                for line in f:
                    if line.strip() and not line.startswith('#'):
                        fields = line.strip().split(':')
                        if len(fields) >= 3:
                            uid = fields[2]
                            if uid in uid_counts:
                                uid_counts[uid].append(fields[0])
                            else:
                                uid_counts[uid] = [fields[0]]
            
            duplicates = {uid: users for uid, users in uid_counts.items() if len(users) > 1}
            
            if not duplicates:
                status = "PASS"
                current = "No duplicate UIDs found"
            else:
                status = "FAIL"
                duplicate_info = [f"UID {uid}: {', '.join(users)}" for uid, users in duplicates.items()]
                current = f"Duplicate UIDs: {'; '.join(duplicate_info)}"
            
            return {
                "status": status,
                "current": current,
                "expected": "No duplicate UIDs",
                "evidence": f"Checked {len(uid_counts)} UIDs, Duplicates: {len(duplicates)}"
            }
            
        except Exception as e:
            return {
                "status": "ERROR",
                "current": "Error checking duplicate UIDs",
                "expected": "No duplicate UIDs",
                "evidence": str(e)
            }
    
    def check_duplicate_gids(self, group_file: str) -> Dict[str, Any]:
        """Check for duplicate GIDs"""
        try:
            if not os.path.exists(group_file):
                return {
                    "status": "FAIL",
                    "current": "group file not found",
                    "expected": "No duplicate GIDs",
                    "evidence": f"File {group_file} does not exist"
                }
            
            gid_counts = {}
            
            with open(group_file, 'r') as f:
                for line in f:
                    if line.strip() and not line.startswith('#'):
                        fields = line.strip().split(':')
                        if len(fields) >= 3:
                            gid = fields[2]
                            if gid in gid_counts:
                                gid_counts[gid].append(fields[0])
                            else:
                                gid_counts[gid] = [fields[0]]
            
            duplicates = {gid: groups for gid, groups in gid_counts.items() if len(groups) > 1}
            
            if not duplicates:
                status = "PASS"
                current = "No duplicate GIDs found"
            else:
                status = "FAIL"
                duplicate_info = [f"GID {gid}: {', '.join(groups)}" for gid, groups in duplicates.items()]
                current = f"Duplicate GIDs: {'; '.join(duplicate_info)}"
            
            return {
                "status": status,
                "current": current,
                "expected": "No duplicate GIDs",
                "evidence": f"Checked {len(gid_counts)} GIDs, Duplicates: {len(duplicates)}"
            }
            
        except Exception as e:
            return {
                "status": "ERROR",
                "current": "Error checking duplicate GIDs",
                "expected": "No duplicate GIDs",
                "evidence": str(e)
            }
    
    def check_duplicate_usernames(self, passwd_file: str) -> Dict[str, Any]:
        """Check for duplicate usernames"""
        try:
            if not os.path.exists(passwd_file):
                return {
                    "status": "FAIL",
                    "current": "passwd file not found",
                    "expected": "No duplicate usernames",
                    "evidence": f"File {passwd_file} does not exist"
                }
            
            username_counts = {}
            
            with open(passwd_file, 'r') as f:
                for line in f:
                    if line.strip() and not line.startswith('#'):
                        fields = line.strip().split(':')
                        if len(fields) >= 1:
                            username = fields[0]
                            username_counts[username] = username_counts.get(username, 0) + 1
            
            duplicates = {user: count for user, count in username_counts.items() if count > 1}
            
            if not duplicates:
                status = "PASS"
                current = "No duplicate usernames found"
            else:
                status = "FAIL"
                current = f"Duplicate usernames: {', '.join(duplicates.keys())}"
            
            return {
                "status": status,
                "current": current,
                "expected": "No duplicate usernames",
                "evidence": f"Checked {len(username_counts)} usernames, Duplicates: {len(duplicates)}"
            }
            
        except Exception as e:
            return {
                "status": "ERROR",
                "current": "Error checking duplicate usernames",
                "expected": "No duplicate usernames",
                "evidence": str(e)
            }
    
    def check_duplicate_groupnames(self, group_file: str) -> Dict[str, Any]:
        """Check for duplicate group names"""
        try:
            if not os.path.exists(group_file):
                return {
                    "status": "FAIL",
                    "current": "group file not found",
                    "expected": "No duplicate group names",
                    "evidence": f"File {group_file} does not exist"
                }
            
            groupname_counts = {}
            
            with open(group_file, 'r') as f:
                for line in f:
                    if line.strip() and not line.startswith('#'):
                        fields = line.strip().split(':')
                        if len(fields) >= 1:
                            groupname = fields[0]
                            groupname_counts[groupname] = groupname_counts.get(groupname, 0) + 1
            
            duplicates = {group: count for group, count in groupname_counts.items() if count > 1}
            
            if not duplicates:
                status = "PASS"
                current = "No duplicate group names found"
            else:
                status = "FAIL"
                current = f"Duplicate group names: {', '.join(duplicates.keys())}"
            
            return {
                "status": status,
                "current": current,
                "expected": "No duplicate group names",
                "evidence": f"Checked {len(groupname_counts)} group names, Duplicates: {len(duplicates)}"
            }
            
        except Exception as e:
            return {
                "status": "ERROR",
                "current": "Error checking duplicate group names",
                "expected": "No duplicate group names",
                "evidence": str(e)
            }
    
    def check_user_home_dirs(self, passwd_file: str, min_uid: int) -> Dict[str, Any]:
        """Check user home directory configuration"""
        try:
            # Validate path to prevent traversal attacks
            if not self._validate_path(passwd_file):
                return {
                    "status": "FAIL",
                    "current": "Invalid file path",
                    "expected": "All interactive users have valid home directories",
                    "evidence": f"File path {passwd_file} is not allowed"
                }
            
            if not os.path.exists(passwd_file):
                return {
                    "status": "FAIL",
                    "current": "passwd file not found",
                    "expected": "All interactive users have valid home directories",
                    "evidence": f"File {passwd_file} does not exist"
                }
            
            issues = []
            checked_users = 0
            
            with open(passwd_file, 'r') as f:
                for line in f:
                    if line.strip() and not line.startswith('#'):
                        fields = line.strip().split(':')
                        if len(fields) >= 6:
                            username = fields[0]
                            uid = int(fields[2]) if fields[2].isdigit() else 0
                            home_dir = fields[5]
                            
                            # Check interactive users (UID >= min_uid)
                            if uid >= min_uid:
                                checked_users += 1
                                if not home_dir or home_dir == '/':
                                    issues.append(f"{username}: no home directory assigned")
                                elif not os.path.exists(home_dir):
                                    issues.append(f"{username}: home directory {home_dir} does not exist")
            
            if not issues:
                status = "PASS"
                current = f"All {checked_users} interactive users have valid home directories"
            else:
                status = "FAIL"
                current = f"Home directory issues: {'; '.join(issues[:5])}{'...' if len(issues) > 5 else ''}"
            
            return {
                "status": status,
                "current": current,
                "expected": "All interactive users have valid home directories",
                "evidence": f"Checked {checked_users} interactive users, Issues: {len(issues)}"
            }
            
        except Exception as e:
            return {
                "status": "ERROR",
                "current": "Error checking user home directories",
                "expected": "All interactive users have valid home directories",
                "evidence": str(e)
            }
    
    def check_user_dot_files(self, passwd_file: str, min_uid: int, max_permissions: str) -> Dict[str, Any]:
        """Check user dot file permissions"""
        try:
            if not os.path.exists(passwd_file):
                return {
                    "status": "FAIL",
                    "current": "passwd file not found",
                    "expected": f"User dot files have proper permissions ({max_permissions})",
                    "evidence": f"File {passwd_file} does not exist"
                }
            
            issues = []
            checked_users = 0
            
            with open(passwd_file, 'r') as f:
                for line in f:
                    if line.strip() and not line.startswith('#'):
                        fields = line.strip().split(':')
                        if len(fields) >= 6:
                            username = fields[0]
                            uid = int(fields[2]) if fields[2].isdigit() else 0
                            home_dir = fields[5]
                            
                            # Check interactive users (UID >= min_uid)
                            if uid >= min_uid and os.path.exists(home_dir):
                                checked_users += 1
                                
                                # Check common dot files
                                dot_files = ['.bashrc', '.bash_profile', '.profile', '.cshrc', '.tcshrc']
                                for dot_file in dot_files:
                                    dot_path = os.path.join(home_dir, dot_file)
                                    if os.path.exists(dot_path):
                                        try:
                                            file_stat = os.stat(dot_path)
                                            file_mode = oct(file_stat.st_mode)[-3:]
                                            # Check if group or other have write permission
                                            if int(file_mode[1]) & 2 or int(file_mode[2]) & 2:
                                                issues.append(f"{username}:{dot_file} ({file_mode})")
                                        except:
                                            continue
            
            if not issues:
                status = "PASS"
                current = f"All dot files for {checked_users} users have proper permissions"
            else:
                status = "FAIL"
                current = f"Dot file permission issues: {'; '.join(issues[:5])}{'...' if len(issues) > 5 else ''}"
            
            return {
                "status": status,
                "current": current,
                "expected": f"User dot files have proper permissions ({max_permissions})",
                "evidence": f"Checked {checked_users} interactive users, Issues: {len(issues)}"
            }
            
        except Exception as e:
            return {
                "status": "ERROR",
                "current": "Error checking user dot files",
                "expected": f"User dot files have proper permissions ({max_permissions})",
                "evidence": str(e)
            }
    
    def load_milestone(self, milestone_file: str) -> List[Dict[str, Any]]:
        """Load CIS controls from milestone file"""
        milestone_path = self.milestones_dir / milestone_file
        
        if not milestone_path.exists():
            print(f"Warning: Milestone file {milestone_file} not found")
            return []
        
        try:
            with open(milestone_path, 'r') as f:
                milestone_data = json.load(f)
            return milestone_data.get('controls', [])
        except Exception as e:
            print(f"Error loading milestone {milestone_file}: {e}")
            return []
    
    def execute_control(self, control: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single CIS control check"""
        control_id = control.get('id', 'Unknown')
        control_type = control.get('type', 'Manual')
        
        result = {
            "id": control_id,
            "title": control.get('title', ''),
            "section": control.get('section', ''),
            "cis_reference": control.get('cis_reference', ''),
            "cis_control_id": control.get('cis_control_id', ''),
            "reference_note": control.get('reference_note', ''),
            "profile": control.get('profile', 'Level1'),
            "status": "MANUAL",
            "current": "",
            "expected": "",
            "evidence": ""
        }
        
        # Skip if not in selected profile
        if self.profile == "Level1" and control.get('profile') == "Level2":
            result["status"] = "SKIPPED"
            result["evidence"] = f"Skipped (Profile: {control.get('profile')})"
            return result
        
        try:
            if control_type == "FilePermission":
                check_result = self.check_file_permissions(
                    control.get('file_path', ''),
                    control.get('expected_mode', ''),
                    control.get('expected_owner'),
                    control.get('expected_group')
                )
            elif control_type == "Service":
                check_result = self.check_service_status(
                    control.get('service_name', ''),
                    control.get('expected_status', '')
                )
            elif control_type == "KernelParameter":
                check_result = self.check_kernel_parameter(
                    control.get('parameter', ''),
                    control.get('expected_value', '')
                )
            elif control_type == "Package":
                check_result = self.check_package_installed(
                    control.get('package_name', ''),
                    control.get('should_be_installed', True)
                )
            elif control_type == "ConfigFile":
                check_result = self.check_config_file(
                    control.get('file_path', ''),
                    control.get('pattern', ''),
                    control.get('expected_match', True)
                )
            elif control_type == "KernelModule":
                check_result = self.check_kernel_module(
                    control.get('module_name', ''),
                    control.get('expected_status', '')
                )
            elif control_type == "MountOption":
                check_result = self.check_mount_option(
                    control.get('mount_point', ''),
                    control.get('required_option', '')
                )
            elif control_type == "MountPoint":
                check_result = self.check_mount_point(
                    control.get('mount_point', ''),
                    control.get('expected_status', '')
                )
            elif control_type == "BootParameter":
                check_result = self.check_boot_parameters(
                    control.get('parameters', []),
                    control.get('config_file', '/etc/default/grub')
                )
            elif control_type == "AppArmorProfile":
                check_result = self.check_apparmor_profiles(
                    control.get('expected_modes', []),
                    control.get('check_unconfined', False)
                )
            elif control_type == "CoreDumpRestriction":
                check_result = self.check_core_dump_restriction(
                    control.get('expected_setting', ''),
                    control.get('limits_files', [])
                )
            elif control_type == "ServiceNotInUse":
                check_result = self.check_service_not_in_use(
                    control.get('service_names', []),
                    control.get('package_names', [])
                )
            elif control_type == "MTALocalOnly":
                check_result = self.check_mta_local_only(
                    control.get('config_file', ''),
                    control.get('expected_setting', '')
                )
            elif control_type == "WirelessInterface":
                check_result = self.check_wireless_interface(
                    control.get('expected_status', '')
                )
            elif control_type == "MultiKernelParameter":
                check_result = self.check_multi_kernel_parameters(
                    control.get('parameters', [])
                )
            elif control_type == "SingleFirewall":
                check_result = self.check_single_firewall(
                    control.get('firewall_utilities', [])
                )
            elif control_type == "UFWStatus":
                check_result = self.check_ufw_status(
                    control.get('expected_status', '')
                )
            elif control_type == "UFWLoopback":
                check_result = self.check_ufw_loopback(
                    control.get('expected_rules', [])
                )
            elif control_type == "UFWOpenPorts":
                check_result = self.check_ufw_open_ports(
                    control.get('check_open_ports', False)
                )
            elif control_type == "UFWDefaultPolicy":
                check_result = self.check_ufw_default_policy(
                    control.get('expected_policies', {})
                )
            elif control_type == "NftablesTable":
                check_result = self.check_nftables_table(
                    control.get('expected_families', [])
                )
            elif control_type == "NftablesBaseChains":
                check_result = self.check_nftables_base_chains(
                    control.get('required_hooks', [])
                )
            elif control_type == "SSHPrivateKeys":
                check_result = self.check_ssh_private_keys(
                    control.get('key_pattern', ''),
                    control.get('expected_mode', ''),
                    control.get('expected_owner', ''),
                    control.get('expected_group', '')
                )
            elif control_type == "SSHPublicKeys":
                check_result = self.check_ssh_public_keys(
                    control.get('key_pattern', ''),
                    control.get('expected_mode', ''),
                    control.get('expected_owner', ''),
                    control.get('expected_group', '')
                )
            elif control_type == "SSHDConfig":
                check_result = self.check_sshd_config(
                    control.get('config_file', ''),
                    control.get('check_parameters', []),
                    control.get('expected_values', {}),
                    control.get('require_one_of', False),
                    control.get('validate_crypto', False)
                )
            elif control_type == "SudoConfig":
                check_result = self.check_sudo_config(
                    control.get('config_files', []),
                    control.get('required_setting', ''),
                    control.get('prohibited_setting', '')
                )
            elif control_type == "PAMConfig":
                check_result = self.check_pam_config(
                    control.get('config_file', ''),
                    control.get('required_setting', '')
                )
            elif control_type == "SingleLoggingSystem":
                check_result = self.check_single_logging_system(
                    control.get('logging_services', [])
                )
            elif control_type == "JournaldConfig":
                check_result = self.check_journald_config(
                    control.get('config_file', ''),
                    control.get('parameter', ''),
                    control.get('expected_value', '')
                )
            elif control_type == "RsyslogConfig":
                check_result = self.check_rsyslog_config(
                    control.get('config_files', []),
                    control.get('prohibited_directives', [])
                )
            elif control_type == "LogFilePermissions":
                check_result = self.check_log_file_permissions(
                    control.get('log_directory', ''),
                    control.get('expected_file_permissions', ''),
                    control.get('expected_dir_permissions', '')
                )
            elif control_type == "MultiPackage":
                check_result = self.check_multi_packages(
                    control.get('package_names', []),
                    control.get('should_be_installed', True)
                )
            elif control_type == "AuditdConfig":
                check_result = self.check_auditd_config(
                    control.get('config_file', ''),
                    control.get('parameter', ''),
                    control.get('expected_value', ''),
                    control.get('check_configured', False)
                )
            elif control_type == "AuditRule":
                check_result = self.check_audit_rule(
                    control.get('rule_file', ''),
                    control.get('expected_rules', [])
                )
            elif control_type == "AuditLogPermissions":
                check_result = self.check_audit_log_permissions(
                    control.get('log_directory', ''),
                    control.get('expected_file_mode', ''),
                    control.get('expected_owner', ''),
                    control.get('expected_group', '')
                )
            elif control_type == "CronJob":
                check_result = self.check_cron_job(
                    control.get('cron_user', ''),
                    control.get('expected_job', ''),
                    control.get('job_description', '')
                )
            elif control_type == "AIDEConfig":
                check_result = self.check_aide_config(
                    control.get('config_file', ''),
                    control.get('monitored_tools', [])
                )
            elif control_type == "WorldWritableFiles":
                check_result = self.check_world_writable_files(
                    control.get('search_paths', []),
                    control.get('exclude_paths', [])
                )
            elif control_type == "OrphanedFiles":
                check_result = self.check_orphaned_files(
                    control.get('search_paths', []),
                    control.get('exclude_paths', [])
                )
            elif control_type == "ShadowedPasswords":
                check_result = self.check_shadowed_passwords(
                    control.get('passwd_file', '')
                )
            elif control_type == "EmptyPasswords":
                check_result = self.check_empty_passwords(
                    control.get('shadow_file', '')
                )
            elif control_type == "GroupConsistency":
                check_result = self.check_group_consistency(
                    control.get('passwd_file', ''),
                    control.get('group_file', '')
                )
            elif control_type == "EmptyGroup":
                check_result = self.check_empty_group(
                    control.get('group_name', ''),
                    control.get('group_file', '')
                )
            elif control_type == "DuplicateUIDs":
                check_result = self.check_duplicate_uids(
                    control.get('passwd_file', '')
                )
            elif control_type == "DuplicateGIDs":
                check_result = self.check_duplicate_gids(
                    control.get('group_file', '')
                )
            elif control_type == "DuplicateUsernames":
                check_result = self.check_duplicate_usernames(
                    control.get('passwd_file', '')
                )
            elif control_type == "DuplicateGroupnames":
                check_result = self.check_duplicate_groupnames(
                    control.get('group_file', '')
                )
            elif control_type == "UserHomeDirs":
                check_result = self.check_user_home_dirs(
                    control.get('passwd_file', ''),
                    control.get('min_uid', 1000)
                )
            elif control_type == "UserDotFiles":
                check_result = self.check_user_dot_files(
                    control.get('passwd_file', ''),
                    control.get('min_uid', 1000),
                    control.get('max_permissions', 'go-w')
                )
            else:
                # Manual check
                check_result = {
                    "status": "MANUAL",
                    "current": "Manual verification required",
                    "expected": control.get('expected', 'See CIS documentation'),
                    "evidence": "This control requires manual verification"
                }
            
            result.update(check_result)
            
        except Exception as e:
            result["status"] = "ERROR"
            result["evidence"] = f"Error executing control: {str(e)}"
        
        return result
    
    def scan_milestones(self, milestone_files: List[str] = None) -> None:
        """Scan specified milestone files or all available"""
        if milestone_files is None:
            milestone_files = [f for f in os.listdir(self.milestones_dir) if f.endswith('.json')]
        
        # Color codes
        GREEN = '\033[92m'
        BLUE = '\033[94m'
        YELLOW = '\033[93m'
        RED = '\033[91m'
        CYAN = '\033[96m'
        BOLD = '\033[1m'
        RESET = '\033[0m'
        
        # Display signature
        print(f"{CYAN}{BOLD}")
        print("██╗   ██╗██╗     ██╗███████╗███╗   ██╗███████╗██╗  ██╗")
        print("██║   ██║██║     ██║██╔════╝████╗  ██║██╔════╝╚██╗██╔╝")
        print("██║   ██║██║     ██║█████╗  ██╔██╗ ██║█████╗   ╚███╔╝ ")
        print("╚██╗ ██╔╝██║██   ██║██╔══╝  ██║╚██╗██║██╔══╝   ██╔██╗ ")
        print(" ╚████╔╝ ██║╚█████╔╝███████╗██║ ╚████║███████╗██╔╝ ██╗")
        print("  ╚═══╝  ╚═╝ ╚════╝ ╚══════╝╚═╝  ╚═══╝╚══════╝╚═╝  ╚═╝")
        print(f"{RESET}")
        print(f"{BOLD}{BLUE}                 Vijenex CIS Scanner{RESET}")
        print(f"{YELLOW}           Enterprise Linux Security Compliance{RESET}")
        print(f"{CYAN}═" * 60 + f"{RESET}")
        
        print(f"{BOLD}🔍 Starting CIS Compliance Scan...{RESET}")
        print(f"{BLUE}📋 Profile:{RESET} {YELLOW}{self.profile}{RESET}")
        print(f"{BLUE}🐧 Distribution:{RESET} {GREEN}{self.system_info['distribution']}{RESET}")
        print(f"{BLUE}📁 Milestones:{RESET} {CYAN}{len(milestone_files)}{RESET}")
        print(f"{CYAN}─" * 60 + f"{RESET}")
        
        for milestone_file in milestone_files:
            print(f"{BOLD}{BLUE}📄 Processing {milestone_file}...{RESET}")
            controls = self.load_milestone(milestone_file)
            
            for control in controls:
                result = self.execute_control(control)
                self.results.append(result)
                
                if result["status"] == "PASS":
                    status_symbol = f"{GREEN}✓{RESET}"
                elif result["status"] == "FAIL":
                    status_symbol = f"{RED}✗{RESET}"
                elif result["status"] == "MANUAL":
                    status_symbol = f"{YELLOW}⚠{RESET}"
                else:
                    status_symbol = f"{CYAN}?{RESET}"
                
                print(f"  {status_symbol} {CYAN}{result['id']}{RESET}: {result['title'][:50]}...")
        
        print(f"{CYAN}─" * 60 + f"{RESET}")
        
        # Summary with colors
        pass_count = sum(1 for r in self.results if r["status"] == "PASS")
        fail_count = sum(1 for r in self.results if r["status"] == "FAIL")
        manual_count = sum(1 for r in self.results if r["status"] == "MANUAL")
        
        print(f"{BOLD}🎯 Scan Completed Successfully!{RESET}")
        print(f"{GREEN}✓ Passed:{RESET} {GREEN}{pass_count}{RESET}")
        print(f"{RED}✗ Failed:{RESET} {RED}{fail_count}{RESET}")
        print(f"{YELLOW}⚠ Manual:{RESET} {YELLOW}{manual_count}{RESET}")
        print(f"{BOLD}📊 Total Controls:{RESET} {CYAN}{len(self.results)}{RESET}")
    
    def generate_html_report(self) -> str:
        """Generate HTML compliance report"""
        pass_count = sum(1 for r in self.results if r["status"] == "PASS")
        fail_count = sum(1 for r in self.results if r["status"] == "FAIL")
        manual_count = sum(1 for r in self.results if r["status"] == "MANUAL")
        
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Linux CIS Compliance Report - Vijenex Security Platform</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .header {{ background: #2c3e50; color: white; padding: 20px; text-align: center; }}
        .summary {{ display: flex; justify-content: space-around; margin: 20px 0; }}
        .metric {{ text-align: center; padding: 20px; border-radius: 5px; }}
        .pass {{ background: #d4edda; color: #155724; }}
        .fail {{ background: #f8d7da; color: #721c24; }}
        .manual {{ background: #fff3cd; color: #856404; }}
        .system-info {{ background: #f8f9fa; padding: 15px; margin: 20px 0; }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background: #f2f2f2; }}
        .status-pass {{ color: #28a745; font-weight: bold; }}
        .status-fail {{ color: #dc3545; font-weight: bold; }}
        .status-manual {{ color: #ffc107; font-weight: bold; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Linux CIS Compliance Report</h1>
        <p>Powered by Vijenex Security Platform</p>
    </div>
    
    <div class="system-info">
        <h3>System Information</h3>
        <p><strong>Hostname:</strong> {self.system_info['hostname']}</p>
        <p><strong>IP Address:</strong> {self.system_info['ip_address']}</p>
        <p><strong>Distribution:</strong> {self.system_info['distribution']}</p>
        <p><strong>Architecture:</strong> {self.system_info['architecture']}</p>
        <p><strong>Scan Date:</strong> {self.system_info['scan_date']}</p>
        <p><strong>Profile:</strong> {self.profile}</p>
    </div>
    
    <div class="summary">
        <div class="metric pass">
            <h3>{pass_count}</h3>
            <p>Passed</p>
        </div>
        <div class="metric fail">
            <h3>{fail_count}</h3>
            <p>Failed</p>
        </div>
        <div class="metric manual">
            <h3>{manual_count}</h3>
            <p>Manual</p>
        </div>
    </div>
    
    <h3>Detailed Results</h3>
    <table>
        <tr>
            <th>ID</th>
            <th>Control</th>
            <th>Section</th>
            <th>Status</th>
            <th>CIS Reference</th>
            <th>Details</th>
        </tr>
"""
        
        for result in self.results:
            status_class = f"status-{result['status'].lower()}"
            status_symbol = "✓" if result["status"] == "PASS" else "✗" if result["status"] == "FAIL" else "?"
            
            cis_link = f"<a href='{result.get('cis_reference', '#')}' target='_blank'>CIS Benchmark</a>" if result.get('cis_reference') else 'N/A'
            reference_note = result.get('reference_note', 'Refer to official CIS benchmark documentation')
            
            html_content += f"""
        <tr>
            <td>{result['id']}</td>
            <td>{result['title']}</td>
            <td>{result['section']}</td>
            <td class="{status_class}">{status_symbol} {result['status']}</td>
            <td>{cis_link}</td>
            <td>{reference_note}</td>
        </tr>"""
        
        html_content += """
    </table>
</body>
</html>"""
        
        report_path = self.output_dir / "vijenex-cis-report.html"
        with open(report_path, 'w') as f:
            f.write(html_content)
        
        return str(report_path)
    
    def generate_csv_report(self) -> str:
        """Generate CSV compliance report"""
        import csv
        
        report_path = self.output_dir / "vijenex-cis-results.csv"
        
        with open(report_path, 'w', newline='') as csvfile:
            fieldnames = ['ID', 'Control', 'Section', 'Status', 'CIS_Reference', 'Reference_Note']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for result in self.results:
                writer.writerow({
                    'ID': result['id'],
                    'Control': result['title'],
                    'Section': result['section'],
                    'Status': result['status'],
                    'CIS_Reference': result.get('cis_reference', ''),
                    'Reference_Note': result.get('reference_note', 'Refer to official CIS benchmark documentation')
                })
        
        return str(report_path)

def main():
    parser = argparse.ArgumentParser(description='Vijenex CIS - Enterprise Linux Security Compliance Scanner')
    parser.add_argument('--output-dir', help='Output directory for reports (default: ../reports)')
    parser.add_argument('--profile', choices=['Level1', 'Level2'], default='Level1', help='CIS profile level')
    parser.add_argument('--milestones', nargs='+', help='Specific milestone files to scan')
    parser.add_argument('--format', choices=['html', 'csv', 'both'], default='both', help='Report format')
    
    args = parser.parse_args()
    
    # Check if running as root
    if os.geteuid() != 0:
        print("Warning: Running without root privileges. Some checks may fail.")
        print("For complete scanning, run with: sudo vijenex-cis")
        print()
    
    scanner = LinuxCISScanner(args.output_dir, args.profile)
    scanner.scan_milestones(args.milestones)
    
    GREEN = '\033[92m'
    BLUE = '\033[94m'
    YELLOW = '\033[93m'
    BOLD = '\033[1m'
    RESET = '\033[0m'
    
    print(f"\n{BOLD}{BLUE}📊 Generating reports...{RESET}")
    
    if args.format in ['html', 'both']:
        html_report = scanner.generate_html_report()
        print(f"{GREEN}📄 HTML report:{RESET} {html_report}")
    
    if args.format in ['csv', 'both']:
        csv_report = scanner.generate_csv_report()
        print(f"{GREEN}📊 CSV report:{RESET} {csv_report}")
    
    print(f"\n{BOLD}{GREEN}🎉 Vijenex CIS scan completed successfully!{RESET}")

if __name__ == "__main__":
    main()