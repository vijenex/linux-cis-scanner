package controls

import (
	"fmt"
	"os/exec"
	"strings"
)

func CheckSysctlParameter(parameterName, expectedValue string) CheckResult {
	cmd := exec.Command("sysctl", parameterName)
	output, err := cmd.Output()
	
	if err != nil {
		return CheckResult{
			Status:          "ERROR",
			ActualValue:     "Parameter not found",
			EvidenceCommand: fmt.Sprintf("sysctl %s", parameterName),
			Description:     fmt.Sprintf("Failed to read %s", parameterName),
		}
	}
	
	outputStr := strings.TrimSpace(string(output))
	parts := strings.Split(outputStr, "=")
	if len(parts) != 2 {
		return CheckResult{
			Status:          "ERROR",
			ActualValue:     "Invalid output format",
			EvidenceCommand: fmt.Sprintf("sysctl %s", parameterName),
			Description:     "Could not parse sysctl output",
		}
	}
	
	actualValue := strings.TrimSpace(parts[1])
	status := "FAIL"
	if actualValue == expectedValue {
		status = "PASS"
	}
	
	return CheckResult{
		Status:          status,
		ActualValue:     fmt.Sprintf("%s = %s (expected: %s)", parameterName, actualValue, expectedValue),
		EvidenceCommand: fmt.Sprintf("sysctl %s", parameterName),
		Description:     fmt.Sprintf("Kernel parameter %s check", parameterName),
	}
}
