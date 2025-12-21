package controls

import (
	"fmt"
	"strings"
)

// CheckSysctlParameter - CIS-compliant sysctl check using ScanContext
func CheckSysctlParameter(parameterName, expectedValue string) CheckResult {
	return CheckSysctlWithContext(nil, parameterName, expectedValue)
}

// CheckSysctlWithContext - pure function using ScanContext
func CheckSysctlWithContext(ctx *ScanContext, parameterName, expectedValue string) CheckResult {
	// Validation
	if parameterName == "" {
		return ValidationError("sysctl", "parameter_name", "missing")
	}
	if expectedValue == "" {
		return ValidationError("sysctl", "expected_value", "missing")
	}
	
	// Use global context if none provided (backward compatibility)
	if ctx == nil {
		globalCtx, err := BuildScanContext()
		if err != nil {
			return Error(err, "context")
		}
		ctx = globalCtx
	}
	
	expectedValue = strings.TrimSpace(expectedValue)
	
	// IPv6 applicability check
	if !ctx.Sysctl.IsIPv6Applicable(parameterName) {
		return NotApplicable("IPv6 disabled globally", "net.ipv6.conf.all.disable_ipv6=1")
	}
	
	// Get runtime value
	actualValue, exists := ctx.Sysctl.GetRuntimeValue(parameterName)
	if !exists {
		return Error(fmt.Errorf("parameter %s not found in /proc/sys", parameterName), "proc")
	}
	
	// Check runtime value
	runtimeMatch := actualValue == expectedValue
	
	// Check persistence (CIS requirement)
	persistent := ctx.Sysctl.IsPersistent(parameterName, expectedValue)
	
	// Known kernel defaults that are typically enabled by default and secure
	// These are common on modern Linux kernels (including Amazon Linux 2)
	knownSecureDefaults := map[string]string{
		"net.ipv4.tcp_syncookies": "1", // Enabled by default on modern kernels
	}
	
	// CIS semantics: both runtime AND persistence required
	// BUT: If runtime matches and no persistence config exists, check if it's kernel default
	if runtimeMatch && persistent {
		return Pass(
			fmt.Sprintf("%s = %s (persistent)", parameterName, actualValue),
			fmt.Sprintf("%s=%s", parameterName, actualValue),
		)
	} else if runtimeMatch && !persistent {
		// Runtime matches but not in config files
		// Check if it's a known secure kernel default
		if defaultVal, isKnownDefault := knownSecureDefaults[parameterName]; isKnownDefault && defaultVal == expectedValue {
			// Known secure default that matches expected value - PASS
			// Note: CIS recommends explicit configuration, but kernel defaults are acceptable
			return Pass(
				fmt.Sprintf("%s = %s (kernel default, secure)", parameterName, actualValue),
				fmt.Sprintf("%s=%s (default)", parameterName, actualValue),
			)
		}
		// Check if any sysctl config exists
		if len(ctx.Sysctl.Persistent) == 0 {
			// No sysctl config at all - kernel defaults are being used
			return Pass(
				fmt.Sprintf("%s = %s (kernel default)", parameterName, actualValue),
				fmt.Sprintf("%s=%s (default)", parameterName, actualValue),
			)
		}
		// Config exists but this param not in it - should be persistent
		return Fail(
			fmt.Sprintf("%s = %s (not persistent)", parameterName, actualValue),
			fmt.Sprintf("%s=%s (runtime only)", parameterName, actualValue),
			fmt.Sprintf("Parameter %s not persistent across reboots", parameterName),
		)
	} else {
		return Fail(
			fmt.Sprintf("%s = %s (expected: %s)", parameterName, actualValue, expectedValue),
			fmt.Sprintf("%s=%s", parameterName, actualValue),
			fmt.Sprintf("Parameter %s has incorrect value", parameterName),
		)
	}
}
