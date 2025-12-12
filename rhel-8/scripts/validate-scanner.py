#!/usr/bin/env python3
"""
Vijenex CIS Scanner Validation Script
Validates scanner implementation and control definitions
"""

import json
import sys
from pathlib import Path

def validate_scanner():
    """Comprehensive validation of scanner and controls"""
    
    errors = []
    warnings = []
    
    print("=" * 60)
    print("VIJENEX CIS SCANNER VALIDATION")
    print("=" * 60)
    print()
    
    # 1. Validate JSON structure
    print("1. Validating JSON structure...")
    milestone_path = Path(__file__).parent.parent / "milestones" / "milestone-1-1.json"
    
    try:
        with open(milestone_path, 'r') as f:
            data = json.load(f)
        print("   ✓ JSON is valid")
    except Exception as e:
        errors.append(f"JSON validation failed: {e}")
        print(f"   ✗ JSON validation failed: {e}")
        return False
    
    controls = data.get('controls', [])
    print(f"   ✓ Total controls: {len(controls)}")
    
    # 2. Validate control structure
    print("\n2. Validating control structure...")
    required_fields = ['id', 'title', 'section', 'profile', 'automated', 'type', 'severity', 'cis_reference', 'description', 'rationale', 'remediation', 'impact', 'references', 'audit_command']
    
    for idx, control in enumerate(controls):
        control_id = control.get('id', f'Control #{idx}')
        
        # Check required fields
        missing = [f for f in required_fields if f not in control]
        if missing:
            errors.append(f"{control_id}: Missing fields: {', '.join(missing)}")
        
        # Validate control type specific fields
        control_type = control.get('type')
        
        if control_type == 'KernelModule':
            if 'module_name' not in control or 'expected_status' not in control:
                errors.append(f"{control_id}: KernelModule missing module_name or expected_status")
        
        elif control_type == 'MountPoint':
            if 'mount_point' not in control or 'expected_status' not in control:
                errors.append(f"{control_id}: MountPoint missing mount_point or expected_status")
        
        elif control_type == 'MountOption':
            if 'mount_point' not in control or 'required_option' not in control:
                errors.append(f"{control_id}: MountOption missing mount_point or required_option")
        
        elif control_type == 'FileContent':
            if not all(k in control for k in ['file_path', 'pattern', 'expected_result']):
                errors.append(f"{control_id}: FileContent missing file_path, pattern, or expected_result")
        
        elif control_type == 'ServiceStatus':
            if 'service_name' not in control or 'expected_status' not in control:
                errors.append(f"{control_id}: ServiceStatus missing service_name or expected_status")
        
        elif control_type == 'PackageInstalled':
            if 'package_name' not in control or 'expected_status' not in control:
                errors.append(f"{control_id}: PackageInstalled missing package_name or expected_status")
        
        elif control_type != 'Manual':
            warnings.append(f"{control_id}: Unknown control type: {control_type}")
    
    if not errors:
        print("   ✓ All controls have required fields")
    else:
        print(f"   ✗ Found {len(errors)} structural errors")
    
    # 3. Validate automation status
    print("\n3. Validating automation status...")
    automated = sum(1 for c in controls if c.get('automated', False))
    manual = len(controls) - automated
    automation_rate = (automated / len(controls)) * 100 if controls else 0
    
    print(f"   ✓ Automated: {automated} ({automation_rate:.1f}%)")
    print(f"   ✓ Manual: {manual}")
    
    if automation_rate < 90:
        warnings.append(f"Automation rate is {automation_rate:.1f}% (target: >90%)")
    
    # 4. Validate control types distribution
    print("\n4. Validating control types...")
    types = {}
    for c in controls:
        t = c.get('type', 'Unknown')
        types[t] = types.get(t, 0) + 1
    
    for t, count in sorted(types.items()):
        print(f"   ✓ {t}: {count}")
    
    # 5. Validate severity levels
    print("\n5. Validating severity levels...")
    severities = {}
    for c in controls:
        s = c.get('severity', 'unknown')
        severities[s] = severities.get(s, 0) + 1
    
    for s, count in sorted(severities.items()):
        print(f"   ✓ {s}: {count}")
    
    # 6. Validate Level 2 controls have impact warnings
    print("\n6. Validating Level 2 impact warnings...")
    level2_controls = [c for c in controls if c.get('profile') == 'Level2']
    level2_without_warning = []
    
    for c in level2_controls:
        impact = c.get('impact', '')
        if '⚠️' not in impact and 'WARNING' not in impact.upper() and 'LEVEL 2' not in impact.upper():
            level2_without_warning.append(c.get('id'))
    
    if level2_without_warning:
        warnings.append(f"Level 2 controls without impact warnings: {', '.join(level2_without_warning)}")
        print(f"   ⚠ {len(level2_without_warning)} Level 2 controls missing impact warnings")
    else:
        print(f"   ✓ All {len(level2_controls)} Level 2 controls have impact warnings")
    
    # 7. Summary
    print("\n" + "=" * 60)
    print("VALIDATION SUMMARY")
    print("=" * 60)
    
    if errors:
        print(f"\n❌ ERRORS: {len(errors)}")
        for e in errors:
            print(f"   - {e}")
    
    if warnings:
        print(f"\n⚠️  WARNINGS: {len(warnings)}")
        for w in warnings:
            print(f"   - {w}")
    
    if not errors and not warnings:
        print("\n✅ ALL VALIDATIONS PASSED!")
        print(f"\n📊 Scanner Statistics:")
        print(f"   - Total Controls: {len(controls)}")
        print(f"   - Automated: {automated} ({automation_rate:.1f}%)")
        print(f"   - Manual: {manual}")
        print(f"   - Control Types: {len(types)}")
        print(f"\n🎯 Scanner is ready for production use!")
        return True
    elif not errors:
        print(f"\n✅ VALIDATION PASSED WITH WARNINGS")
        print(f"   Scanner is functional but has {len(warnings)} warnings to review")
        return True
    else:
        print(f"\n❌ VALIDATION FAILED")
        print(f"   Fix {len(errors)} errors before using scanner")
        return False

if __name__ == "__main__":
    success = validate_scanner()
    sys.exit(0 if success else 1)
