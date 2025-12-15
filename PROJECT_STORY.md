# CIS Linux Scanner - Project Story

## Current Status: ⚠️ PARSER INCOMPLETE

### What Works ✅
- Parser detects control types correctly (Manual: 217 → 7)
- Go scanner compiles and runs
- Binary generates CSV/HTML reports
- Type detection: FileContent=81, ServiceStatus=61, etc.

### What's Broken ❌
- **Parser doesn't extract type-specific fields**
- Milestones missing: `package_name`, `service_name`, `file_path`, `parameter_name`
- Result: 200+ controls show ERROR "Validation failed: missing X"

### Test Results (RHEL 9)
```
Total: 297 controls
PASS: 5 (kernel modules only)
FAIL: 1
ERROR: 200+ (missing fields in milestones)
MANUAL: 20
NOT_APPLICABLE: 70+
```

## Problem Analysis

### Parser Output (Current)
```json
{
  "id": "2.1.3",
  "type": "ServiceStatus",  ✅ Correct type
  "service_name": "",        ❌ MISSING
  "expected_status": ""      ❌ MISSING
}
```

### What Scanner Needs
```json
{
  "id": "2.1.3",
  "type": "ServiceStatus",
  "service_name": "dhcpd",
  "expected_status": "disabled"
}
```

## Next Steps (Priority Order)

### Option 1: Fix Parser (Recommended)
**Effort**: 2-3 hours  
**Impact**: Fixes all 200+ controls

**Tasks**:
1. Parser extracts service names from titles/audit sections
2. Parser extracts file paths from titles
3. Parser extracts sysctl parameters from titles
4. Regenerate all milestones
5. Re-test scanner

### Option 2: Manual Curation
**Effort**: 8-10 hours  
**Impact**: Error-prone, not scalable

### Option 3: Use RHEL 8 Milestones
**Effort**: 1 hour  
**Impact**: Wrong control IDs/titles for RHEL 9

## Recommendation

**Fix the parser** - it's the only scalable solution for Ubuntu 20.04/22.04/24.04 later.

## Parser Fix Requirements

### For Each Control Type:

**ServiceStatus**:
- Extract service name from title: "dhcp server" → `dhcpd`
- Set expected_status: "not in use" → `disabled`

**PackageInstalled**:
- Extract package from title: "ftp client" → `ftp`
- Set expected_status: "not installed" → `not_installed`

**SysctlParameter**:
- Extract parameter from title: "ip forwarding" → `net.ipv4.ip_forward`
- Extract value from audit section: `0`

**FilePermissions**:
- Extract path from title: "/etc/passwd" → `/etc/passwd`
- Extract permissions from audit: `0644`

**FileContent**:
- Extract path from title
- Extract pattern from audit section

## Timeline

**Today**: Fix parser + regenerate milestones  
**Tomorrow**: Test on RHEL 9, validate results  
**Next**: Parse Ubuntu benchmarks

## Files Modified So Far

1. ✅ `parse-cis-rtf.py` - Type detection fixed
2. ✅ `checks.go` - Security fixes applied
3. ✅ `scancontext.go` - GetModuleInfo added
4. ✅ `types.go` - EvidenceCommand added
5. ⏳ `parse-cis-rtf.py` - Field extraction needed

## Commands to Resume

```bash
# Fix parser
cd /Users/sowmya/Desktop/Vijenex/linux-cis-scanner/scripts/parsers
# Edit parse-cis-rtf.py to extract fields

# Regenerate milestones
python3 parse-cis-rtf.py \
  /Users/sowmya/Desktop/CIS-Official-docs/CIS_Red_Hat_Enterprise_Linux_9_Benchmark_v2.0.0.rtf \
  ../../rhel-9/go-scanner/milestones \
  "RHEL 9" "v2.0.0"

# Rebuild binary
cd ../../rhel-9/go-scanner
env CGO_ENABLED=0 GOOS=linux GOARCH=amd64 go build -ldflags="-s -w" -o bin/vijenex-cis-rhel9 cmd/main.go

# Push
git add . && git commit -m "fix: parser field extraction" && git push
```

## Success Criteria

- [ ] ERROR controls < 10
- [ ] PASS + FAIL > 200
- [ ] All automated controls have required fields
- [ ] Scanner runs without validation errors

---
**Last Updated**: Dec 15, 2024 - 20:30  
**Status**: Parser needs field extraction logic
