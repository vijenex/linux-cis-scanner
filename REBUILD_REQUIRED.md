# 🔄 REBUILD REQUIRED

## Issue Fixed
- **Problem**: 43 controls in Ubuntu 24.04 were missing the `automated` field
- **Solution**: Added `automated: true` to all missing controls
- **Result**: All controls now have explicit `automated` field

## Action Required

**You must rebuild the scanner binary on your remote server:**

```bash
cd ~/linux-cis-scanner/ubuntu-24.04/go-scanner
./build.sh
```

Or if you're using the wrapper script:
```bash
cd ~/linux-cis-scanner/ubuntu-24.04/go-scanner
sudo ./vijenex-cis
```

The wrapper will automatically rebuild if needed.

## Expected Results After Rebuild

**Ubuntu 24.04:**
- Total Level 1 controls: 201
- ✅ Automated: 195 (97%)
- ⚠️ Manual: 6 (3%)

**Ubuntu 22.04:**
- Total Level 1 controls: 299
- ✅ Automated: 285 (95%)
- ⚠️ Manual: 14 (5%)

## What Changed

1. Added `automated: true` to 43 controls in Ubuntu 24.04
2. Added `automated: true` to 270 controls in Ubuntu 22.04
3. All controls now have explicit `automated` field (no more missing fields)

The scanner will now correctly identify automated controls and only show 6-14 manual controls (policy decisions only).

