#!/usr/bin/env python3
"""
██╗   ██╗██╗     ██╗███████╗███╗   ██╗███████╗██╗  ██╗
██║   ██║██║     ██║██╔════╝████╗  ██║██╔════╝╚██╗██╔╝
██║   ██║██║     ██║█████╗  ██╔██╗ ██║█████╗   ╚███╔╝ 
╚██╗ ██╔╝██║██   ██║██╔══╝  ██║╚██╗██║██╔══╝   ██╔██╗ 
 ╚████╔╝ ██║╚█████╔╝███████╗██║ ╚████║███████╗██╔╝ ██╗
  ╚═══╝  ╚═╝ ╚════╝ ╚══════╝╚═╝  ╚═══╝╚══════╝╚═╝  ╚═╝

                Vijenex CIS Scanner Test
           Powered by Vijenex Security Platform
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

# Import the scanner class from the main module
# Import directly from the file
exec(open('linux-cis-scanner.py').read())

def test_vijenex_scanner():
    """Test basic Vijenex CIS scanner functionality"""
    print("🔍 Testing Vijenex CIS Scanner...")
    print("-" * 50)
    
    # Initialize Vijenex scanner
    scanner = LinuxCISScanner(output_dir="./vijenex-test-reports", profile="Level1")
    
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
    
    print("\n" + "-" * 50)
    print("🎉 Vijenex CIS scanner test completed!")
    print("Run the full scanner with: sudo python3 linux-cis-scanner.py")

if __name__ == "__main__":
    test_vijenex_scanner()