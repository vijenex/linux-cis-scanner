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
	
	// IPv6 applicability check - if IPv6 is disabled, skip IPv6-specific parameters
	// (These should be excluded from milestones, but if they appear, return PASS)
	if !ctx.Sysctl.IsIPv6Applicable(parameterName) {
		return Pass(
			"IPv6 disabled globally - parameter not applicable",
			"net.ipv6.conf.all.disable_ipv6=1",
		)
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
	
	// CIS semantics: both runtime AND persistence required
	if runtimeMatch && persistent {
		return Pass(
			fmt.Sprintf("%s = %s (persistent)", parameterName, actualValue),
			fmt.Sprintf("%s=%s", parameterName, actualValue),
		)
	} else if runtimeMatch && !persistent {
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

