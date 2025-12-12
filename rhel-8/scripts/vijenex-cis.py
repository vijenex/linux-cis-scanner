#!/usr/bin/env python3
"""
██████╗ ██╗  ██╗███████╗██╗          █████╗ 
██╔══██╗██║  ██║██╔════╝██║         ██╔══██╗
██████╔╝███████║█████╗  ██║         ╚█████╔╝
██╔══██╗██╔══██║██╔══╝  ██║          ╚═══██╗
██║  ██║██║  ██║███████╗███████╗    █████╔╝ 
╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝╚══════╝    ╚════╝  

    .--.
   |o_o |     Vijenex CIS Scanner
   |:_/ |     Red Hat Enterprise Linux 8
  //   \ \    Security Compliance Automation
 (|     | )
/'\_   _/`\
\___)=(___/

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
import re
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import glob

class RHEL8CISScanner:
    """RHEL 8 CIS compliance scanner engine"""
    
    def __init__(self, output_dir: str = None, profile: str = "Level1"):
        if output_dir is None:
            output_dir = "./reports"
            
        self.output_dir = Path(output_dir)
        self.profile = profile
        self.results = []
        self.system_info = self._get_system_info()
        
        current_path = Path(__file__).parent
        self.milestones_dir = current_path.parent / "milestones"
        
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
    def _get_system_info(self) -> Dict[str, Any]:
        """Collect system information"""
        try:
            hostname = socket.gethostname()
            ip_address = socket.gethostbyname(hostname)
        except:
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
            "scanner_version": "1.0.0-rhel8"
        }
    
    def _get_distribution(self) -> str:
        """Get Linux distribution"""
        try:
            with open('/etc/os-release', 'r') as f:
                for line in f:
                    if line.startswith('PRETTY_NAME='):
                        return line.split('=')[1].strip().strip('"')
        except:
            pass
        return "Red Hat Enterprise Linux 8"
    
    def _run_command(self, command: str, shell: bool = True) -> Tuple[str, str, int]:
        """Execute system command"""
        try:
            safe_commands = ['systemctl', 'sysctl', 'rpm', 'lsmod', 'modinfo', 'modprobe', 'findmnt', 'grep', 'getenforce', 'sestatus', 'firewall-cmd', 'ss', 'crontab', 'find', 'auditctl', 'grubby', 'dnf', 'yum', 'cat']
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
        except Exception as e:
            return "", f"Command error: {str(e)}", 1
    
    def _validate_path(self, file_path: str) -> bool:
        """Validate file path"""
        try:
            resolved_path = os.path.realpath(file_path)
            allowed_prefixes = ['/etc/', '/var/', '/usr/', '/bin/', '/sbin/', '/lib/', '/opt/', '/home/', '/root/', '/proc/', '/sys/', '/boot/']
            return any(resolved_path.startswith(prefix) for prefix in allowed_prefixes)
        except:
            return False
    
    def check_kernel_module(self, module_name: str, expected_status: str) -> Dict[str, Any]:
        """Check kernel module status"""
        try:
            blacklist_found = False
            modprobe_dirs = ['/etc/modprobe.d/', '/lib/modprobe.d/', '/usr/lib/modprobe.d/']
            
            for modprobe_dir in modprobe_dirs:
                if os.path.exists(modprobe_dir):
                    try:
                        for conf_file in os.listdir(modprobe_dir):
                            if conf_file.endswith('.conf'):
                                conf_path = os.path.join(modprobe_dir, conf_file)
                                if self._validate_path(conf_path):
                                    try:
                                        with open(conf_path, 'r', encoding='utf-8', errors='ignore') as f:
                                            content = f.read()
                                            if re.search(f'install\\s+{re.escape(module_name)}\\s+/bin/(true|false)', content):
                                                blacklist_found = True
                                                break
                                    except:
                                        continue
                    except:
                        continue
                if blacklist_found:
                    break
            
            stdout, stderr, returncode = self._run_command(f"lsmod | grep -w {module_name}")
            module_loaded = returncode == 0 and module_name in stdout
            
            stdout, stderr, returncode = self._run_command(f"modinfo {module_name}")
            module_exists = returncode == 0
            
            if expected_status == "not_available":
                if blacklist_found and not module_loaded:
                    status = "PASS"
                    actual_value = "Module blacklisted and not loaded"
                elif not module_exists:
                    status = "PASS"
                    actual_value = "Module not available in kernel"
                elif module_loaded:
                    status = "FAIL"
                    actual_value = "Module is loaded"
                else:
                    status = "FAIL"
                    actual_value = "Module available but not blacklisted"
            else:
                status = "FAIL"
                actual_value = f"Unexpected expected_status: {expected_status}"
            
            return {
                "status": status,
                "actual_value": actual_value,
                "evidence_command": f"lsmod | grep {module_name}; modprobe -n -v {module_name}",
                "description": f"Module {module_name}: blacklisted={blacklist_found}, loaded={module_loaded}"
            }
            
        except Exception as e:
            return {
                "status": "ERROR",
                "actual_value": "Error checking module",
                "evidence_command": f"lsmod | grep {module_name}",
                "description": str(e)
            }
    
    def check_mount_point(self, mount_point: str, expected_status: str) -> Dict[str, Any]:
        """Check if mount point exists"""
        try:
            mount_found = False
            device_info = ""
            
            if not self._validate_path('/proc/mounts'):
                return {
                    "status": "ERROR",
                    "actual_value": "Cannot access mount information",
                    "evidence_command": "findmnt",
                    "description": "Access to /proc/mounts denied"
                }
            
            with open('/proc/mounts', 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    parts = line.strip().split()
                    if len(parts) >= 2 and parts[1] == mount_point:
                        mount_found = True
                        device_info = parts[0]
                        break
            
            if expected_status == "separate_partition":
                if mount_found and not device_info.startswith('/dev/loop'):
                    status = "PASS"
                    actual_value = f"Separate partition: {device_info}"
                elif mount_found:
                    status = "PASS"
                    actual_value = f"Mounted: {device_info}"
                else:
                    status = "FAIL"
                    actual_value = "Not a separate partition"
            else:
                status = "FAIL"
                actual_value = f"Unexpected expected_status: {expected_status}"
            
            return {
                "status": status,
                "actual_value": actual_value,
                "evidence_command": f"findmnt {mount_point}",
                "description": f"Mount point {mount_point} verification"
            }
            
        except Exception as e:
            return {
                "status": "ERROR",
                "actual_value": "Error checking mount point",
                "evidence_command": f"findmnt {mount_point}",
                "description": str(e)
            }
    
    def check_mount_option(self, mount_point: str, required_option: str) -> Dict[str, Any]:
        """Check mount option"""
        try:
            current_options = []
            mount_found = False
            
            with open('/proc/mounts', 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    parts = line.strip().split()
                    if len(parts) >= 4 and parts[1] == mount_point:
                        mount_found = True
                        current_options = parts[3].split(',')
                        break
            
            if not mount_found:
                return {
                    "status": "FAIL",
                    "actual_value": "Mount point not found",
                    "evidence_command": f"findmnt {mount_point}",
                    "description": f"Mount point {mount_point} is not mounted"
                }
            
            option_present = required_option in current_options
            status = "PASS" if option_present else "FAIL"
            
            return {
                "status": status,
                "actual_value": f"Options: {','.join(current_options)}",
                "evidence_command": f"findmnt -n {mount_point} | grep -v {required_option}",
                "description": f"Mount {mount_point}: {required_option} {'found' if option_present else 'missing'}"
            }
            
        except Exception as e:
            return {
                "status": "ERROR",
                "actual_value": "Error checking mount options",
                "evidence_command": f"findmnt {mount_point}",
                "description": str(e)
            }
    
    def check_service_status(self, service_name: str, expected_status: str) -> Dict[str, Any]:
        """Check if service is enabled/disabled"""
        try:
            stdout, stderr, returncode = self._run_command(f"systemctl is-enabled {service_name}")
            
            if expected_status == "enabled":
                if returncode == 0 and "enabled" in stdout:
                    status = "PASS"
                    actual_value = f"Service {service_name} is enabled"
                else:
                    status = "FAIL"
                    actual_value = f"Service {service_name} is not enabled: {stdout.strip()}"
            elif expected_status == "disabled":
                if returncode != 0 or "disabled" in stdout or "masked" in stdout:
                    status = "PASS"
                    actual_value = f"Service {service_name} is disabled/masked"
                else:
                    status = "FAIL"
                    actual_value = f"Service {service_name} is enabled"
            else:
                status = "FAIL"
                actual_value = f"Unknown expected_status: {expected_status}"
            
            return {
                "status": status,
                "actual_value": actual_value,
                "evidence_command": f"systemctl is-enabled {service_name}",
                "description": f"Service {service_name} status check"
            }
        except Exception as e:
            return {
                "status": "ERROR",
                "actual_value": "Error checking service",
                "evidence_command": f"systemctl is-enabled {service_name}",
                "description": str(e)
            }
    
    def check_package_installed(self, package_name: str, expected_status: str) -> Dict[str, Any]:
        """Check if package is installed"""
        try:
            stdout, stderr, returncode = self._run_command(f"rpm -q {package_name}")
            
            if expected_status == "installed":
                if returncode == 0:
                    status = "PASS"
                    actual_value = f"Package {package_name} is installed: {stdout.strip()}"
                else:
                    status = "FAIL"
                    actual_value = f"Package {package_name} is not installed"
            elif expected_status == "not_installed":
                if returncode != 0:
                    status = "PASS"
                    actual_value = f"Package {package_name} is not installed"
                else:
                    status = "FAIL"
                    actual_value = f"Package {package_name} is installed: {stdout.strip()}"
            else:
                status = "FAIL"
                actual_value = f"Unknown expected_status: {expected_status}"
            
            return {
                "status": status,
                "actual_value": actual_value,
                "evidence_command": f"rpm -q {package_name}",
                "description": f"Package {package_name} installation check"
            }
        except Exception as e:
            return {
                "status": "ERROR",
                "actual_value": "Error checking package",
                "evidence_command": f"rpm -q {package_name}",
                "description": str(e)
            }
    
    def check_sysctl_parameter(self, parameter: str, expected_value: str) -> Dict[str, Any]:
        """Check sysctl kernel parameter"""
        try:
            stdout, stderr, returncode = self._run_command(f"sysctl {parameter}")
            
            if returncode == 0:
                actual_value = stdout.strip().split('=')[-1].strip()
                
                if actual_value == expected_value:
                    status = "PASS"
                    result_msg = f"{parameter} = {actual_value}"
                else:
                    status = "FAIL"
                    result_msg = f"{parameter} = {actual_value} (expected: {expected_value})"
            else:
                status = "FAIL"
                result_msg = f"Parameter {parameter} not found"
            
            return {
                "status": status,
                "actual_value": result_msg,
                "evidence_command": f"sysctl {parameter}",
                "description": f"Kernel parameter {parameter} check"
            }
        except Exception as e:
            return {
                "status": "ERROR",
                "actual_value": "Error checking sysctl",
                "evidence_command": f"sysctl {parameter}",
                "description": str(e)
            }
    
    def check_file_permissions(self, file_path: str, expected_mode: str = None, expected_owner: str = None, expected_group: str = None) -> Dict[str, Any]:
        """Check file permissions, owner, and group"""
        try:
            if not self._validate_path(file_path):
                return {
                    "status": "ERROR",
                    "actual_value": "Invalid file path",
                    "evidence_command": f"stat {file_path}",
                    "description": "File path validation failed"
                }
            
            if not os.path.exists(file_path):
                return {
                    "status": "FAIL",
                    "actual_value": "File does not exist",
                    "evidence_command": f"stat {file_path}",
                    "description": f"File {file_path} not found"
                }
            
            stat_info = os.stat(file_path)
            actual_mode = oct(stat_info.st_mode)[-4:]
            actual_owner = pwd.getpwuid(stat_info.st_uid).pw_name
            actual_group = grp.getgrgid(stat_info.st_gid).gr_name
            
            issues = []
            if expected_mode and actual_mode != expected_mode:
                issues.append(f"mode={actual_mode} (expected {expected_mode})")
            if expected_owner and actual_owner != expected_owner:
                issues.append(f"owner={actual_owner} (expected {expected_owner})")
            if expected_group and actual_group != expected_group:
                issues.append(f"group={actual_group} (expected {expected_group})")
            
            if issues:
                status = "FAIL"
                result_msg = f"{file_path}: " + ", ".join(issues)
            else:
                status = "PASS"
                result_msg = f"{file_path}: {actual_mode} {actual_owner}:{actual_group}"
            
            return {
                "status": status,
                "actual_value": result_msg,
                "evidence_command": f"stat -c '%a %U:%G' {file_path}",
                "description": f"File permissions check for {file_path}"
            }
        except Exception as e:
            return {
                "status": "ERROR",
                "actual_value": "Error checking file permissions",
                "evidence_command": f"stat {file_path}",
                "description": str(e)
            }
    
    def check_file_content(self, file_path: str, pattern: str, expected_result: str) -> Dict[str, Any]:
        """Check file content using grep pattern"""
        try:
            if not file_path:
                return {
                    "status": "ERROR",
                    "actual_value": "No file path specified",
                    "evidence_command": "N/A",
                    "description": "File path is required"
                }
            
            if not self._validate_path(file_path):
                return {
                    "status": "ERROR",
                    "actual_value": "Invalid file path",
                    "evidence_command": f"cat {file_path}",
                    "description": "File path validation failed"
                }
            
            stdout, stderr, returncode = self._run_command(f"grep -Pi -- '{pattern}' {file_path}")
            
            if expected_result == "found":
                if returncode == 0 and stdout.strip():
                    status = "PASS"
                    actual_value = f"Pattern found: {stdout.strip()[:100]}"
                else:
                    status = "FAIL"
                    actual_value = "Pattern not found"
            elif expected_result == "not_found":
                if returncode != 0 or not stdout.strip():
                    status = "PASS"
                    actual_value = "Pattern not found (as expected)"
                else:
                    status = "FAIL"
                    actual_value = f"Pattern found: {stdout.strip()[:100]}"
            else:
                status = "FAIL"
                actual_value = f"Unknown expected_result: {expected_result}"
            
            return {
                "status": status,
                "actual_value": actual_value,
                "evidence_command": f"grep -Pi -- '{pattern}' {file_path}",
                "description": f"File content check: {file_path}"
            }
        except Exception as e:
            return {
                "status": "ERROR",
                "actual_value": "Error checking file content",
                "evidence_command": f"grep -Pi -- '{pattern}' {file_path}",
                "description": str(e)
            }
    
    def load_milestone(self, milestone_file: str) -> List[Dict[str, Any]]:
        """Load controls from milestone file"""
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
        """Execute a single CIS control"""
        control_id = control.get('id', 'Unknown')
        control_type = control.get('type', 'Manual')
        
        result = {
            "id": control_id,
            "title": control.get('title', ''),
            "section": control.get('section', ''),
            "cis_reference": control.get('cis_reference', ''),
            "remediation": control.get('remediation', 'Refer to CIS Benchmark documentation'),
            "description": control.get('description', ''),
            "profile": control.get('profile', 'Level1'),
            "status": "MANUAL",
            "actual_value": "",
            "evidence_command": ""
        }
        
        if self.profile == "Level1" and control.get('profile') == "Level2":
            result["status"] = "SKIPPED"
            result["description"] = f"Skipped (Profile: {control.get('profile')})"
            return result
        
        try:
            if control_type == "KernelModule":
                check_result = self.check_kernel_module(
                    control.get('module_name', ''),
                    control.get('expected_status', '')
                )
            elif control_type == "MountPoint":
                check_result = self.check_mount_point(
                    control.get('mount_point', ''),
                    control.get('expected_status', '')
                )
            elif control_type == "MountOption":
                check_result = self.check_mount_option(
                    control.get('mount_point', ''),
                    control.get('required_option', '')
                )
            elif control_type == "ServiceStatus":
                check_result = self.check_service_status(
                    control.get('service_name', ''),
                    control.get('expected_status', '')
                )
            elif control_type == "PackageInstalled":
                check_result = self.check_package_installed(
                    control.get('package_name', ''),
                    control.get('expected_status', '')
                )
            elif control_type == "FileContent":
                check_result = self.check_file_content(
                    control.get('file_path', ''),
                    control.get('pattern', ''),
                    control.get('expected_result', '')
                )
            elif control_type == "SysctlParameter":
                check_result = self.check_sysctl_parameter(
                    control.get('parameter', ''),
                    control.get('expected_value', '')
                )
            elif control_type == "FilePermissions":
                check_result = self.check_file_permissions(
                    control.get('file_path', ''),
                    control.get('expected_mode', None),
                    control.get('expected_owner', None),
                    control.get('expected_group', None)
                )
            elif control_type == "Manual" or control_type == "ServiceConfig" or control_type == "ServiceUser":
                check_result = {
                    "status": "MANUAL",
                    "actual_value": "Manual verification required",
                    "evidence_command": "N/A",
                    "description": "This control requires manual verification"
                }
            else:
                check_result = {
                    "status": "MANUAL",
                    "actual_value": f"Unknown control type: {control_type}",
                    "evidence_command": "N/A",
                    "description": f"Control type '{control_type}' not implemented"
                }
            
            result.update(check_result)
            
        except Exception as e:
            result["status"] = "ERROR"
            result["description"] = f"Error executing control: {str(e)}"
        
        return result
    
    def scan_milestones(self, milestone_files: List[str] = None) -> None:
        """Scan milestone files"""
        if milestone_files is None:
            milestone_files = sorted([f for f in os.listdir(self.milestones_dir) if f.endswith('.json')])
        
        GREEN = '\033[92m'
        BLUE = '\033[94m'
        YELLOW = '\033[93m'
        RED = '\033[91m'
        CYAN = '\033[96m'
        BOLD = '\033[1m'
        RESET = '\033[0m'
        
        print()
        print(f"{CYAN}============================================================={RESET}")
        print(f"{CYAN}                        VIJENEX                              {RESET}")
        print(f"{BOLD}      {self.system_info['distribution']} CIS Scanner           {RESET}")
        print(f"{YELLOW}           Powered by Vijenex Security Platform             {RESET}")
        print(f"{CYAN}        https://github.com/vijenex/linux-cis-scanner        {RESET}")
        print(f"{CYAN}============================================================={RESET}")
        print()
        
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
        
        pass_count = sum(1 for r in self.results if r["status"] == "PASS")
        fail_count = sum(1 for r in self.results if r["status"] == "FAIL")
        manual_count = sum(1 for r in self.results if r["status"] == "MANUAL")
        
        success_rate = round((pass_count / len(self.results)) * 100, 1) if self.results else 0
        
        print()
        print(f"{CYAN}============================================================={RESET}")
        print(f"{CYAN}                    SCAN COMPLETED                           {RESET}")
        print(f"{CYAN}============================================================={RESET}")
        print(f"Total Checks: {len(self.results)}")
        print(f"Passed: {GREEN}{pass_count}{RESET}")
        print(f"Failed: {RED}{fail_count}{RESET}")
        print(f"Manual: {YELLOW}{manual_count}{RESET}")
        print(f"Success Rate: {YELLOW}{success_rate}%{RESET}")
        print(f"{CYAN}============================================================={RESET}")
        print()
    
    def generate_csv_report(self) -> str:
        """Generate CSV report"""
        import csv
        
        report_path = self.output_dir / "vijenex-cis-results.csv"
        
        with open(report_path, 'w', newline='') as csvfile:
            fieldnames = ['Id', 'Title', 'Section', 'Status', 'CISReference', 'Remediation', 'Description']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for result in self.results:
                writer.writerow({
                    'Id': result['id'],
                    'Title': result['title'],
                    'Section': result['section'],
                    'Status': result['status'],
                    'CISReference': result.get('cis_reference', 'Refer to CIS Benchmark documentation'),
                    'Remediation': result.get('remediation', 'Refer to CIS Benchmark documentation'),
                    'Description': result.get('description', 'Security control verification')
                })
        
        return str(report_path)
    
    def generate_html_report(self) -> str:
        """Generate HTML report"""
        pass_count = sum(1 for r in self.results if r["status"] == "PASS")
        fail_count = sum(1 for r in self.results if r["status"] == "FAIL")
        manual_count = sum(1 for r in self.results if r["status"] == "MANUAL")
        skipped_count = sum(1 for r in self.results if r["status"] == "SKIPPED")
        
        # Calculate severity breakdown for failures
        severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0, "unknown": 0}
        for r in self.results:
            if r["status"] == "FAIL":
                sev = r.get("severity", "unknown").lower()
                if sev in severity_counts:
                    severity_counts[sev] += 1
                else:
                    severity_counts["unknown"] += 1
        
        compliance_score = round((pass_count / len(self.results)) * 100, 2) if self.results else 0
        
        html_content = f"""<!DOCTYPE html>
<html>
<head>
    <title>RHEL 8 CIS Compliance Report - Vijenex</title>
    <meta charset="UTF-8">
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #f5f5f5; }}
        .container {{ max-width: 1400px; margin: 0 auto; background: white; }}
        .header {{ background: linear-gradient(135deg, #c00 0%, #8b0000 100%); color: white; padding: 30px; text-align: center; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .header h1 {{ font-size: 32px; margin-bottom: 10px; }}
        .header p {{ font-size: 14px; opacity: 0.9; }}
        .info-section {{ padding: 20px 30px; background: #f8f9fa; border-bottom: 1px solid #dee2e6; }}
        .info-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; }}
        .info-item {{ background: white; padding: 12px; border-radius: 4px; border-left: 3px solid #c00; }}
        .info-label {{ font-size: 11px; color: #6c757d; text-transform: uppercase; font-weight: 600; }}
        .info-value {{ font-size: 14px; color: #212529; margin-top: 4px; }}
        .summary {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 20px; padding: 30px; }}
        .metric {{ text-align: center; padding: 25px; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); transition: transform 0.2s; }}
        .metric:hover {{ transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0,0,0,0.15); }}
        .metric h3 {{ font-size: 36px; margin-bottom: 8px; }}
        .metric p {{ font-size: 14px; text-transform: uppercase; font-weight: 600; }}
        .pass {{ background: #d4edda; color: #155724; }}
        .fail {{ background: #f8d7da; color: #721c24; }}
        .manual {{ background: #fff3cd; color: #856404; }}
        .skipped {{ background: #e2e3e5; color: #383d41; }}
        .score {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; }}
        .severity-section {{ padding: 20px 30px; background: #fff; border-bottom: 1px solid #dee2e6; }}
        .severity-title {{ font-size: 18px; margin-bottom: 15px; color: #212529; }}
        .severity-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(120px, 1fr)); gap: 10px; }}
        .severity-item {{ padding: 12px; border-radius: 4px; text-align: center; }}
        .sev-critical {{ background: #721c24; color: white; }}
        .sev-high {{ background: #dc3545; color: white; }}
        .sev-medium {{ background: #ffc107; color: #212529; }}
        .sev-low {{ background: #17a2b8; color: white; }}
        .sev-unknown {{ background: #6c757d; color: white; }}
        .controls-section {{ padding: 30px; }}
        .control-card {{ background: white; border: 1px solid #dee2e6; border-radius: 6px; margin-bottom: 15px; overflow: hidden; transition: box-shadow 0.2s; }}
        .control-card:hover {{ box-shadow: 0 4px 12px rgba(0,0,0,0.1); }}
        .control-header {{ padding: 15px 20px; background: #f8f9fa; border-bottom: 1px solid #dee2e6; display: flex; justify-content: space-between; align-items: center; cursor: pointer; }}
        .control-id {{ font-weight: 700; color: #c00; font-size: 14px; }}
        .control-title {{ flex: 1; margin: 0 15px; font-size: 14px; color: #212529; }}
        .status-badge {{ padding: 4px 12px; border-radius: 12px; font-size: 12px; font-weight: 600; text-transform: uppercase; }}
        .status-pass {{ background: #28a745; color: white; }}
        .status-fail {{ background: #dc3545; color: white; }}
        .status-manual {{ background: #ffc107; color: #212529; }}
        .status-skipped {{ background: #6c757d; color: white; }}
        .control-body {{ padding: 20px; display: none; }}
        .control-body.active {{ display: block; }}
        .detail-section {{ margin-bottom: 15px; }}
        .detail-label {{ font-size: 12px; font-weight: 600; color: #6c757d; text-transform: uppercase; margin-bottom: 5px; }}
        .detail-content {{ font-size: 14px; color: #212529; line-height: 1.6; }}
        .remediation-box {{ background: #f8f9fa; padding: 15px; border-left: 4px solid #c00; border-radius: 4px; font-family: 'Courier New', monospace; font-size: 13px; white-space: pre-wrap; }}
        .impact-warning {{ background: #fff3cd; padding: 12px; border-left: 4px solid #ffc107; border-radius: 4px; margin-top: 10px; }}
        .footer {{ padding: 20px; text-align: center; background: #f8f9fa; color: #6c757d; font-size: 12px; border-top: 1px solid #dee2e6; }}
        @media print {{ .control-body {{ display: block !important; }} }}
    </style>
    <script>
        function toggleControl(id) {{
            const body = document.getElementById('control-' + id);
            body.classList.toggle('active');
        }}
    </script>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>RHEL 8 CIS Compliance Report</h1>
            <p>Powered by Vijenex Security Platform | https://vijenex.com</p>
        </div>
        
        <div class="info-section">
            <div class="info-grid">
                <div class="info-item">
                    <div class="info-label">Hostname</div>
                    <div class="info-value">{self.system_info['hostname']}</div>
                </div>
                <div class="info-item">
                    <div class="info-label">IP Address</div>
                    <div class="info-value">{self.system_info['ip_address']}</div>
                </div>
                <div class="info-item">
                    <div class="info-label">Distribution</div>
                    <div class="info-value">{self.system_info['distribution']}</div>
                </div>
                <div class="info-item">
                    <div class="info-label">Scan Date</div>
                    <div class="info-value">{self.system_info['scan_date']}</div>
                </div>
                <div class="info-item">
                    <div class="info-label">Profile</div>
                    <div class="info-value">CIS {self.profile}</div>
                </div>
                <div class="info-item">
                    <div class="info-label">Scanner Version</div>
                    <div class="info-value">{self.system_info['scanner_version']}</div>
                </div>
            </div>
        </div>
        
        <div class="summary">
            <div class="metric score">
                <h3>{compliance_score}%</h3>
                <p>Compliance Score</p>
            </div>
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
                <p>Manual Review</p>
            </div>
            <div class="metric skipped">
                <h3>{skipped_count}</h3>
                <p>Skipped</p>
            </div>
        </div>
        
        <div class="severity-section">
            <div class="severity-title">Severity of Failed Rules</div>
            <div class="severity-grid">
                <div class="severity-item sev-critical">
                    <div style="font-size: 24px; font-weight: bold;">{severity_counts['critical']}</div>
                    <div style="font-size: 11px; margin-top: 4px;">CRITICAL</div>
                </div>
                <div class="severity-item sev-high">
                    <div style="font-size: 24px; font-weight: bold;">{severity_counts['high']}</div>
                    <div style="font-size: 11px; margin-top: 4px;">HIGH</div>
                </div>
                <div class="severity-item sev-medium">
                    <div style="font-size: 24px; font-weight: bold;">{severity_counts['medium']}</div>
                    <div style="font-size: 11px; margin-top: 4px;">MEDIUM</div>
                </div>
                <div class="severity-item sev-low">
                    <div style="font-size: 24px; font-weight: bold;">{severity_counts['low']}</div>
                    <div style="font-size: 11px; margin-top: 4px;">LOW</div>
                </div>
                <div class="severity-item sev-unknown">
                    <div style="font-size: 24px; font-weight: bold;">{severity_counts['unknown']}</div>
                    <div style="font-size: 11px; margin-top: 4px;">UNKNOWN</div>
                </div>
            </div>
        </div>
        
        <div class="controls-section">
            <h2 style="margin-bottom: 20px; color: #212529;">Detailed Control Results</h2>
"""
        
        for idx, result in enumerate(self.results):
            status_class = f"status-{result['status'].lower()}"
            impact = result.get('impact', '')
            has_warning = '⚠️' in impact or 'WARNING' in impact.upper()
            
            html_content += f"""
            <div class="control-card">
                <div class="control-header" onclick="toggleControl('{idx}')">
                    <span class="control-id">{result['id']}</span>
                    <span class="control-title">{result['title']}</span>
                    <span class="status-badge {status_class}">{result['status']}</span>
                </div>
                <div id="control-{idx}" class="control-body">
                    <div class="detail-section">
                        <div class="detail-label">Section</div>
                        <div class="detail-content">{result.get('section', 'N/A')}</div>
                    </div>
                    <div class="detail-section">
                        <div class="detail-label">CIS Reference</div>
                        <div class="detail-content">{result.get('cis_reference', 'N/A')}</div>
                    </div>
                    <div class="detail-section">
                        <div class="detail-label">Description</div>
                        <div class="detail-content">{result.get('description', 'N/A')}</div>
                    </div>"""
            
            if result['status'] == 'FAIL':
                html_content += f"""
                    <div class="detail-section">
                        <div class="detail-label">Current Value</div>
                        <div class="detail-content">{result.get('actual_value', 'N/A')}</div>
                    </div>
                    <div class="detail-section">
                        <div class="detail-label">Remediation</div>
                        <div class="remediation-box">{result.get('remediation', 'Refer to CIS Benchmark documentation')}</div>
                    </div>"""
            
            if has_warning:
                html_content += f"""
                    <div class="impact-warning">
                        <strong>⚠️ Impact Warning:</strong><br>
                        {impact}
                    </div>"""
            
            html_content += """
                </div>
            </div>
"""
        
        html_content += f"""
        </div>
        
        <div class="footer">
            <p>Generated by Vijenex CIS Scanner v{self.system_info['scanner_version']} | Scan Date: {self.system_info['scan_date']}</p>
            <p>This report is based on CIS Red Hat Enterprise Linux 8 Benchmark v4.0.0</p>
            <p style="margin-top: 10px;">⚠️ Do not attempt to implement any settings without first testing in a non-operational environment.</p>
        </div>
    </div>
</body>
</html>"""
        
        report_path = self.output_dir / "vijenex-cis-report.html"
        with open(report_path, 'w') as f:
            f.write(html_content)
        
        return str(report_path)

def main():
    parser = argparse.ArgumentParser(description='Vijenex CIS - RHEL 8 Security Compliance Scanner')
    parser.add_argument('--output-dir', help='Output directory for reports')
    parser.add_argument('--profile', choices=['Level1', 'Level2'], default='Level1', help='CIS profile level')
    parser.add_argument('--milestones', nargs='+', help='Specific milestone files to scan')
    parser.add_argument('--format', choices=['html', 'csv', 'both'], default='both', help='Report format')
    parser.add_argument('--read-only', action='store_true', help='Read-only mode (safe for production)')
    
    args = parser.parse_args()
    
    if args.read_only:
        print("\n⚠️  READ-ONLY MODE: Scanner will only read system state, no changes will be made.\n")
    
    if os.geteuid() != 0:
        print("Warning: Running without root privileges. Some checks may fail.")
        print("For complete scanning, run with: sudo vijenex-cis")
        print()
    
    scanner = RHEL8CISScanner(args.output_dir, args.profile)
    scanner.scan_milestones(args.milestones)
    
    GREEN = '\033[92m'
    BLUE = '\033[94m'
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
