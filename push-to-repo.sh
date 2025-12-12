#!/bin/bash
# Push Vijenex CIS Scanner to Repository

cd /Users/satish.korra/Desktop/Linux-CIS-Audit-code

# Add all files
git add .

# Commit with message
git commit -m "feat: Add 234 automated controls with 8 control types

- Added 234 automated controls (91% of OpenSCAP target)
- Implemented 8 control types: KernelModule, MountPoint, MountOption, ServiceStatus, PackageInstalled, FileContent, SysctlParameter, FilePermissions
- Created 48 milestone files organized by CIS section
- Added automated control extraction tool (auto-add-controls.py)
- Professional HTML reports with severity breakdown
- Comprehensive documentation (README, INSTRUCTIONS, QUICK_START)

Ready for RHEL 8 testing and OpenSCAP comparison."

# Push to remote
git push origin main

echo ""
echo "✅ Pushed to repository!"
echo ""
echo "Next: Clone on RHEL 8 machine and run:"
echo "  sudo python3 rhel-8/scripts/vijenex-cis.py --profile Level1"
