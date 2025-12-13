package controls

import (
	"fmt"
	"os/exec"
	"strings"
)

func CheckSysctlParameter(parameterName, expectedValue string) CheckResult {
	if parameterName == "" {
		return CheckResult{
			Status:          "ERROR",
			ActualValue:     "No parameter name specified",
			EvidenceCommand: "N/A",
			Description:     "Parameter name is required",
		}
	}
	
	cmd := exec.Command("sysctl", parameterName)
	output, err := cmd.CombinedOutput()
	outputStr := strings.TrimSpace(string(output))
	
	if err != nil {
		return CheckResult{
			Status:          "FAIL",
			ActualValue:     fmt.Sprintf("Parameter not found or not readable: %s", outputStr),
			EvidenceCommand: fmt.Sprintf("sysctl %s", parameterName),
			Description:     fmt.Sprintf("Failed to read %s", parameterName),
		}
	}
	
	// Parse output: "parameter = value" or "parameter=value"
	parts := strings.SplitN(outputStr, "=", 2)
	if len(parts) != 2 {
		return CheckResult{
			Status:          "ERROR",
			ActualValue:     fmt.Sprintf("Invalid output: %s", outputStr),
			EvidenceCommand: fmt.Sprintf("sysctl %s", parameterName),
			Description:     "Could not parse sysctl output",
		}
	}
	
	actualValue := strings.TrimSpace(parts[1])
	expectedValue = strings.TrimSpace(expectedValue)
	
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
