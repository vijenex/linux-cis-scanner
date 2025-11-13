#!/usr/bin/env python3
"""
Test script for Linux CIS Scanner
Verifies basic functionality without requiring root privileges
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from linux_cis_scanner import LinuxCISScanner

def test_scanner():
    """Test basic scanner functionality"""
    print("Testing Linux CIS Scanner...")
    print("-" * 40)
    
    # Initialize scanner
    scanner = LinuxCISScanner(output_dir="./test-reports", profile="Level1")
    
    # Test system info collection
    print("System Information:")
    for key, value in scanner.system_info.items():
        print(f"  {key}: {value}")
    
    print("\n" + "-" * 40)
    
    # Test individual check methods
    print("Testing check methods:")
    
    # Test file permission check (should work without root)
    result = scanner.check_file_permissions("/etc/passwd", "644", "root", "root")
    print(f"File permission check: {result['status']}")
    
    # Test package check
    result = scanner.check_package_installed("bash", True)
    print(f"Package check (bash): {result['status']}")
    
    # Test kernel parameter check
    result = scanner.check_kernel_parameter("kernel.randomize_va_space", "2")
    print(f"Kernel parameter check: {result['status']}")
    
    # Test config file check
    result = scanner.check_config_file("/etc/passwd", "root", True)
    print(f"Config file check: {result['status']}")
    
    print("\n" + "-" * 40)
    print("Basic functionality test completed!")
    print("Run the full scanner with: sudo python3 linux-cis-scanner.py")

if __name__ == "__main__":
    test_scanner()