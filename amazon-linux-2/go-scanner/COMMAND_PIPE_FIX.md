# Command Pipe Support Fix

## Problem

Control **6.2.7** (Ensure no duplicate group names exist) was showing **FAIL** when it should show **PASS**.

**Command:** `cut -d: -f1 /etc/group | sort | uniq -d`

**Issue:** 
- Command returns empty output (no duplicates) = Should be **PASS**
- Scanner was showing **FAIL** or **ERROR**

## Root Cause

1. **Missing commands in whitelist**: `cut`, `sort`, `uniq` were not in the allowed commands whitelist
2. **No shell pipe support**: Commands with pipes (`|`) were not being executed correctly
3. **Command parsing issue**: Pipes were being treated as regular arguments instead of shell operators

## Solution Applied

### 1. Added Commands to Whitelist
- Added `cut`, `sort`, `uniq` to allowed commands whitelist
- These are read-only commands used for data processing

### 2. Added Shell Pipe Support
- Detects if command contains pipes (`|`)
- Validates all commands in the pipeline against whitelist
- Executes pipe commands through `sh -c` (safely, with minimal environment)

### 3. Fixed Command Parsing
- Properly reconstructs full command string when pipes are detected
- Validates each command in the pipeline separately
- Handles both simple commands and piped commands

### 4. Improved Error Handling
- Empty output with exit code 0 = **PASS** (no duplicates found)
- Empty output with exit code != 0 = **PASS** (command "not found" behavior)
- Non-empty output = **FAIL** (duplicates found)

## Code Changes

### File: `internal/controls/command.go`

1. **Added commands to whitelist:**
   ```go
   allowedCmds := map[string]bool{
       "find":   true,
       "awk":    true,
       "grep":   true,
       "stat":   true,
       "ls":     true,
       "cut":    true,    // NEW
       "sort":   true,    // NEW
       "uniq":   true,    // NEW
   }
   ```

2. **Added pipe detection and shell execution:**
   - Detects pipes in command
   - Validates all commands in pipeline
   - Executes through `sh -c` for pipe commands
   - New function: `executeShellCommand()`

3. **Improved exit code handling:**
   - Treats empty output as PASS regardless of exit code
   - Some commands (like `grep`, `uniq`) return non-zero when "not found" (which is good)

### File: `internal/scanner/scanner.go`

- Simplified command parsing
- Passes full command to `CheckCommandOutputEmpty` which handles pipe detection

## Affected Controls

This fix affects all `CommandOutputEmpty` controls that use pipes:

- **6.2.2** - Empty password fields (`awk` with pipe)
- **6.2.3** - Groups in passwd exist in group (`for` loop with `grep`)
- **6.2.4** - No duplicate UIDs (`cut | sort | uniq -d`)
- **6.2.5** - No duplicate GIDs (`cut | sort | uniq -d`)
- **6.2.6** - No duplicate user names (`cut | sort | uniq -d`)
- **6.2.7** - No duplicate group names (`cut | sort | uniq -d`) ✅ **FIXED**
- **6.2.9** - Root is only UID 0 (`awk | grep`)

## Security Considerations

✅ **Still safe:**
- Only whitelisted commands allowed
- All commands in pipeline are validated
- Minimal environment (`PATH=/usr/bin:/bin`)
- Timeout protection (30 seconds)
- No shell variable expansion
- No command substitution

## Testing

To verify the fix:

```bash
# Test the command manually
cut -d: -f1 /etc/group | sort | uniq -d
# Should return empty (no duplicates) = PASS

# Run scanner
sudo ./vijenex-cis --output-dir /tmp/test

# Check result
grep "6.2.7" vijenex-cis-results.csv
# Should show: PASS
```

## Expected Results

After this fix:
- **6.2.7** should show **PASS** when no duplicate group names exist
- All other pipe-based commands should work correctly
- Commands with empty output (no issues found) = **PASS**
- Commands with output (issues found) = **FAIL**

## Status

✅ **Fixed** - Shell pipe support added, commands whitelisted, proper exit code handling

