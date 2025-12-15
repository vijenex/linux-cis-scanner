# CIS Linux Scanner - Project Story

## Project Overview
Build a Go-based CIS compliance scanner for RHEL and Ubuntu systems that:
- Scans systems against CIS benchmarks
- Generates CSV + HTML reports
- Supports Level 1 and Level 2 profiles
- Zero false positives (critical requirement)

## Repository Structure
```
/Users/sowmya/Desktop/Vijenex/linux-cis-scanner/
├── rhel-8/go-scanner/          # ✅ Complete (reference implementation)
├── rhel-9/go-scanner/          # ✅ Fixed (current work)
│   ├── milestones/             # 297 controls (needs regeneration)
│   ├── internal/controls/      # Scanner logic (security fixes applied)
│   └── cmd/main.go
├── ubuntu-20.04/               # ⏳ Needs controls
├── ubuntu-22.04/               # ⏳ Needs controls
├── ubuntu-24.04/               # ⏳ Needs controls
└── scripts/parsers/
    └── parse-cis-rtf.py        # ✅ Fixed parser
```

## What We Built

### Phase 1: RHEL 9 Parser (COMPLETED ✅)
**Problem**: Parser marked 217/297 controls as "Manual" (73%)

**Root Cause**: Only analyzed control titles, not audit/remediation content

**Solution**: 
- Analyze content windows (audit + remediation sections)
- Pattern matching for control types
- Fixed MountOption vs MountPoint confusion

**Results**:
```
Before: Manual=217, MountOption=2, MountPoint=25
After:  Manual=7,   MountOption=19, MountPoint=6
```

### Phase 2: Security Fixes (COMPLETED ✅)
**Issues Found**:
1. Context leak in CheckKernelModule
2. No input validation (command injection risk)
3. Incomplete symlink validation

**Fixes Applied**:
- Added `defer cancel()` for context cleanup
- Input validation with regex `^[a-zA-Z0-9._/-]+$`
- Length limits (256 chars)

## Current Status

### ✅ Completed
- [x] RHEL 9 parser fixed (7 Manual controls)
- [x] Control type detection (81 FileContent, 61 ServiceStatus, etc.)
- [x] Security fixes in checks.go
- [x] Input validation added

### ⏳ Next Steps
1. **Regenerate RHEL 9 milestones** with fixed parser
2. **Push to repo** (git commit + push)
3. **Test on RHEL 9 machine** (default + hardened)
4. **Validate no false positives**
5. **Parse Ubuntu benchmarks** (20.04, 22.04, 24.04)

## Key Files

### Parser
- **Location**: `scripts/parsers/parse-cis-rtf.py`
- **Purpose**: Extract controls from CIS RTF files
- **Status**: ✅ Fixed (MountOption detection corrected)

### Scanner Core
- **Location**: `rhel-9/go-scanner/internal/controls/checks.go`
- **Purpose**: Execute control checks
- **Status**: ✅ Security fixes applied

### Milestones
- **Location**: `rhel-9/go-scanner/milestones/*.json`
- **Status**: ⚠️ Needs regeneration with fixed parser

## How to Resume Work

### If Context Lost, Run:
```bash
# Show this file
cat /Users/sowmya/Desktop/Vijenex/linux-cis-scanner/PROJECT_STORY.md

# Check current status
cat /Users/sowmya/Desktop/CIS-Official-docs/FINAL_STATUS.md
```

### Quick Commands

**1. Regenerate Milestones**
```bash
cd /Users/sowmya/Desktop/Vijenex/linux-cis-scanner/scripts/parsers
python3 parse-cis-rtf.py \
  /Users/sowmya/Desktop/CIS-Official-docs/CIS_Red_Hat_Enterprise_Linux_9_Benchmark_v2.0.0.rtf \
  ../../rhel-9/go-scanner/milestones \
  "RHEL 9" "v2.0.0"
```

**2. Build Scanner**
```bash
cd /Users/sowmya/Desktop/Vijenex/linux-cis-scanner/rhel-9/go-scanner
./build.sh
```

**3. Test Scanner**
```bash
sudo ./bin/vijenex-cis --profile Level1 --format both
```

**4. Push to Repo**
```bash
cd /Users/sowmya/Desktop/Vijenex/linux-cis-scanner
git add .
git commit -m "fix: parser and security improvements - Manual controls 217→7"
git push origin main
```

## Control Type Distribution (Final)

| Type | Count | Description |
|------|-------|-------------|
| FileContent | 81 | Config file checks (grep patterns) |
| ServiceStatus | 61 | systemctl enabled/disabled |
| FilePermissions | 60 | chmod/chown/stat checks |
| PackageInstalled | 30 | rpm -q checks |
| MountOption | 19 | nodev/nosuid/noexec ✅ |
| SysctlParameter | 17 | Kernel parameters |
| KernelModule | 16 | lsmod/modprobe checks |
| Manual | 7 | Policy/process controls ✅ |
| MountPoint | 6 | Separate partition checks ✅ |
| **TOTAL** | **297** | All RHEL 9 CIS v2.0.0 controls |

## Critical Requirements

1. ✅ **Go-based only** - No Python for scanning
2. ✅ **Level 2 separation** - Level2 controls marked "Not Applicable" in Level1 scans
3. ⏳ **No false positives** - Must validate on real systems
4. ✅ **CSV + HTML output** - Both formats required
5. ✅ **Single binary** - Statically compiled

## Testing Checklist

### Before Production
- [ ] Test on default RHEL 9 install
- [ ] Test on CIS-hardened RHEL 9
- [ ] Verify Level1 vs Level2 separation
- [ ] Check for false positives
- [ ] Validate CSV output format
- [ ] Validate HTML output format
- [ ] Test with non-root user (should fail gracefully)

### Known Edge Cases
- Kernel modules pre-compiled into kernel (should PASS)
- Services masked vs disabled (different semantics)
- Mount options in runtime vs fstab (both required)

## ChatGPT Interactions

### Round 1: Parser Fix Instructions
- **File**: `cis_rtf_parser_fix_instructions.md`
- **Result**: Reduced Manual controls to 16

### Round 2: Security Review
- **File**: `cis_parser_and_scanner_review_summary.md`
- **Result**: Found MountOption issue + security bugs
- **Status**: All issues fixed ✅

## Success Metrics

| Metric | Target | Current | Status |
|--------|--------|---------|--------|
| Manual controls | <15% | 2.4% (7/297) | ✅ |
| MountOption detection | ~19 | 19 | ✅ |
| Security issues | 0 | 0 | ✅ |
| False positives | 0 | Unknown | ⏳ Test needed |

## Next Session Commands

```bash
# 1. Regenerate milestones
cd /Users/sowmya/Desktop/Vijenex/linux-cis-scanner/scripts/parsers
python3 parse-cis-rtf.py /Users/sowmya/Desktop/CIS-Official-docs/CIS_Red_Hat_Enterprise_Linux_9_Benchmark_v2.0.0.rtf ../../rhel-9/go-scanner/milestones "RHEL 9" "v2.0.0"

# 2. Verify counts
find ../../rhel-9/go-scanner/milestones -name "*.json" -exec jq -r '.controls[].type' {} \; | sort | uniq -c

# 3. Push to repo
cd /Users/sowmya/Desktop/Vijenex/linux-cis-scanner
git status
git add .
git commit -m "fix: parser MountOption detection + security fixes"
git push

# 4. Test on RHEL 9
cd rhel-9/go-scanner
./build.sh
sudo ./bin/vijenex-cis --profile Level1 --format both
```

## Repository Info
- **Path**: `/Users/sowmya/Desktop/Vijenex/linux-cis-scanner/`
- **Remote**: (check with `git remote -v`)
- **Branch**: main

---
**Last Updated**: Dec 15, 2024
**Status**: Ready for milestone regeneration + testing
