#!/usr/bin/env python3
"""
██╗   ██╗██╗     ██╗███████╗███╗   ██╗███████╗██╗  ██╗
██║   ██║██║     ██║██╔════╝████╗  ██║██╔════╝╚██╗██╔╝
██║   ██║██║     ██║█████╗  ██╔██╗ ██║█████╗   ╚███╔╝ 
╚██╗ ██╔╝██║██   ██║██╔══╝  ██║╚██╗██║██╔══╝   ██╔██╗ 
 ╚████╔╝ ██║╚█████╔╝███████╗██║ ╚████║███████╗██╔╝ ██╗
  ╚═══╝  ╚═╝ ╚════╝ ╚══════╝╚═╝  ╚═══╝╚══════╝╚═╝  ╚═╝

                    Linux CIS Audit Tool
           Powered by Vijenex Security Platform
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

class LinuxCISScanner:
    """Main Linux CIS compliance scanner engine"""
    
    def __init__(self, output_dir: str = None, profile: str = "Level1"):
        # Default to reports directory in parent folder
        if output_dir is None:
            output_dir = str(Path(__file__).parent.parent / "reports")
        self.output_dir = Path(output_dir)
        self.profile = profile
        self.results = []
        self.system_info = self._get_system_info()
        self.milestones_dir = Path(__file__).parent.parent / "milestones"
        
        # Ensure output directory exists
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
    def _get_system_info(self) -> Dict[str, Any]:
        """Collect system information for reporting"""
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
            "description": control.get('description', ''),
            "impact": control.get('impact', ''),
            "remediation": control.get('remediation', ''),
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
        
        print(f"Starting Linux CIS compliance scan...")
        print(f"Profile: {self.profile}")
        print(f"Distribution: {self.system_info['distribution']}")
        print(f"Milestones: {len(milestone_files)}")
        print("-" * 60)
        
        for milestone_file in milestone_files:
            print(f"Processing {milestone_file}...")
            controls = self.load_milestone(milestone_file)
            
            for control in controls:
                result = self.execute_control(control)
                self.results.append(result)
                
                status_symbol = "✓" if result["status"] == "PASS" else "✗" if result["status"] == "FAIL" else "?"
                print(f"  {status_symbol} {result['id']}: {result['title'][:50]}...")
        
        print("-" * 60)
        print(f"Scan completed. Total controls: {len(self.results)}")
    
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
            <th>Description</th>
            <th>Impact</th>
            <th>Remediation</th>
        </tr>
"""
        
        for result in self.results:
            status_class = f"status-{result['status'].lower()}"
            status_symbol = "✓" if result["status"] == "PASS" else "✗" if result["status"] == "FAIL" else "?"
            
            html_content += f"""
        <tr>
            <td>{result['id']}</td>
            <td>{result['title']}</td>
            <td>{result['section']}</td>
            <td class="{status_class}">{status_symbol} {result['status']}</td>
            <td>{result['description']}</td>
            <td>{result['impact']}</td>
            <td>{result['remediation']}</td>
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
            fieldnames = ['ID', 'Control', 'Section', 'Status', 'Description', 'Impact', 'Remediation']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for result in self.results:
                writer.writerow({
                    'ID': result['id'],
                    'Control': result['title'],
                    'Section': result['section'],
                    'Status': result['status'],
                    'Description': result['description'],
                    'Impact': result['impact'],
                    'Remediation': result['remediation']
                })
        
        return str(report_path)

def main():
    parser = argparse.ArgumentParser(description='Linux CIS Compliance Scanner - Vijenex Security Platform')
    parser.add_argument('--output-dir', help='Output directory for reports (default: ../reports)')
    parser.add_argument('--profile', choices=['Level1', 'Level2'], default='Level1', help='CIS profile level')
    parser.add_argument('--milestones', nargs='+', help='Specific milestone files to scan')
    parser.add_argument('--format', choices=['html', 'csv', 'both'], default='both', help='Report format')
    
    args = parser.parse_args()
    
    # Check if running as root
    if os.geteuid() != 0:
        print("Warning: Running without root privileges. Some checks may fail.")
        print("For complete scanning, run with: sudo python3 linux-cis-scanner.py")
        print()
    
    scanner = LinuxCISScanner(args.output_dir, args.profile)
    scanner.scan_milestones(args.milestones)
    
    # Print summary
    pass_count = sum(1 for r in scanner.results if r["status"] == "PASS")
    fail_count = sum(1 for r in scanner.results if r["status"] == "FAIL")
    manual_count = sum(1 for r in scanner.results if r["status"] == "MANUAL")
    unknown_count = len(scanner.results) - pass_count - fail_count - manual_count
    
    print("\n🎯 Scan Completed Successfully!")
    print(f"✓ Passed: {pass_count}")
    print(f"✗ Failed: {fail_count}")
    print(f"⚠ Manual: {manual_count}")
    if unknown_count > 0:
        print(f"❓ Unknown: {unknown_count}")
    print(f"📊 Total Controls: {len(scanner.results)}")
    
    print("\n📊 Generating reports...")
    
    if args.format in ['html', 'both']:
        html_report = scanner.generate_html_report()
        print(f"📄 HTML report: {html_report}")
    
    if args.format in ['csv', 'both']:
        csv_report = scanner.generate_csv_report()
        print(f"📊 CSV report: {csv_report}")
    
    print("\n🎉 Vijenex CIS scan completed successfully!")

if __name__ == "__main__":
    main()