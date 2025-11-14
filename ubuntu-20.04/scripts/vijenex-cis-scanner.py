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
try:
    from linux_cis_scanner import LinuxCISScanner
except ImportError:
    # Fallback: try importing from current directory
    import importlib.util
    import os
    
    # Validate path to prevent injection attacks
    base_dir = os.path.dirname(os.path.abspath(__file__))
    scanner_filename = 'linux-cis-scanner.py'
    scanner_path = os.path.join(base_dir, scanner_filename)
    
    # Ensure the path is within the expected directory
    if not scanner_path.startswith(base_dir) or '..' in scanner_filename:
        raise ImportError("Invalid scanner path detected")
    
    if os.path.exists(scanner_path):
        spec = importlib.util.spec_from_file_location("linux_cis_scanner", scanner_path)
        linux_cis_scanner = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(linux_cis_scanner)
        LinuxCISScanner = linux_cis_scanner.LinuxCISScanner
    else:
        raise ImportError("Could not find linux-cis-scanner.py module")

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