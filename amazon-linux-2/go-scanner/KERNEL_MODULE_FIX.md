# Kernel Module Detection Fix

## Problem
Kernel modules that don't exist in the kernel (compiled out in cloud AMIs) were showing as FAIL instead of PASS.

## Root Cause
The `buildKernelContext()` function was not properly detecting which modules exist in `/lib/modules`. The module detection was incomplete and didn't check `modules.dep` and `modules.alias` files properly.

## Solution Applied

### 1. Enhanced Module Detection
- **Primary source**: `/lib/modules/$(uname -r)/modules.dep` - Most reliable source
- **Secondary source**: `/lib/modules/$(uname -r)/modules.alias` - For module aliases
- **Fallback**: Walk `/lib/modules/*/kernel/` directories
- **Kernel version detection**: Extract from `/proc/version` or `/proc/sys/kernel/osrelease`

### 2. Fixed Logic Flow
1. Loaded modules → Mark as Available (they definitely exist)
2. Check modules.dep → Mark all modules found as Available
3. Check modules.alias → Mark aliased modules as Available
4. Fallback file walk → Catch modules in non-standard locations

### 3. Check Logic (Already Correct)
The `CheckKernelModule()` logic was already correct:
- If `!modInfo.Exists` → PASS (module not in kernel)
- If `modInfo.Loaded` → FAIL (module is loaded)
- If `modInfo.Exists && !modInfo.Blacklisted` → FAIL (should blacklist)
- If `modInfo.Blacklisted && !modInfo.Loaded` → PASS (properly disabled)

## Expected Results

After this fix:
- **cramfs, hfs, hfsplus, squashfs, udf, usb-storage** → Should show **PASS** if not in kernel
- Only modules that actually exist in `/lib/modules` will be marked as Available
- Modules compiled out of cloud AMI kernels will correctly show as PASS

## Testing

To verify the fix works:
```bash
# Check if modules exist
for mod in cramfs hfs hfsplus squashfs udf usb-storage; do
  echo -n "$mod: "
  if find /lib/modules/$(uname -r) -name "${mod}.ko" 2>/dev/null | grep -q .; then
    echo "EXISTS"
  else
    echo "NOT FOUND (should be PASS)"
  fi
done

# Run scanner
sudo ./vijenex-cis --output-dir /tmp/test

# Check results
grep "1.1.1" vijenex-cis-results.csv | cut -d',' -f1,2,4
```

## Files Modified

1. `internal/controls/scancontext.go`
   - Enhanced `buildKernelContext()` to use modules.dep and modules.alias
   - Added kernel version detection
   - Improved module name extraction

2. `internal/controls/checks.go`
   - Logic was already correct, no changes needed

## Status

✅ **Fixed** - Module detection now properly checks `/lib/modules` using multiple methods

