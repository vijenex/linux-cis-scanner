#!/usr/bin/env python3

import os
import sys
sys.path.append('./ubuntu-22.04/scripts')

# Import the scanner directly
import importlib.util
spec = importlib.util.spec_from_file_location("vijenex_cis", "./ubuntu-22.04/scripts/vijenex-cis.py")
vijenex_cis = importlib.util.module_from_spec(spec)
spec.loader.exec_module(vijenex_cis)
LinuxCISScanner = vijenex_cis.LinuxCISScanner

def test_milestone_loading():
    scanner = LinuxCISScanner('./test-reports', 'Level1')
    
    # Get all milestone files
    milestone_files = [f for f in os.listdir('./ubuntu-22.04/milestones') if f.endswith('.json') and not f.startswith('milestone-template')]
    print(f"Found {len(milestone_files)} milestone files:")
    for f in sorted(milestone_files):
        print(f"  {f}")
    
    print("\nTesting milestone loading:")
    total_controls = 0
    
    for milestone_file in sorted(milestone_files):
        controls = scanner.load_milestone(milestone_file)
        print(f"  {milestone_file}: {len(controls)} controls")
        total_controls += len(controls)
    
    print(f"\nTotal controls across all milestones: {total_controls}")
    
    # Test scanning just first few milestones
    print("\nTesting scan with first 3 milestones:")
    scanner.scan_milestones(sorted(milestone_files)[:3])
    print(f"Results generated: {len(scanner.results)}")
    
    for result in scanner.results[:5]:  # Show first 5 results
        print(f"  {result['id']}: {result['title']}")

if __name__ == "__main__":
    test_milestone_loading()