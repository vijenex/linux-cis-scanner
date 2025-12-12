package controls

import (
	"os"
	"os/exec"
	"strings"
)

func CheckFileContent(filePath, pattern, expectedResult string) CheckResult {
	if filePath == "" {
		return CheckResult{
			Status:          "ERROR",
			ActualValue:     "No file path specified",
			EvidenceCommand: "N/A",
			Description:     "File path is required",
		}
	}

	// Check if file exists
	if _, err := os.Stat(filePath); os.IsNotExist(err) {
		return CheckResult{
			Status:          "FAIL",
			ActualValue:     "File does not exist",
			EvidenceCommand: "ls -la " + filePath,
			Description:     "File not found: " + filePath,
		}
	}

	// Use grep to search for pattern
	cmd := exec.Command("grep", "-Pi", "--", pattern, filePath)
	output, err := cmd.CombinedOutput()
	
	found := err == nil && len(output) > 0

	if expectedResult == "found" {
		if found {
			return CheckResult{
				Status:          "PASS",
				ActualValue:     "Pattern found: " + truncateString(string(output), 100),
				EvidenceCommand: "grep -Pi -- '" + pattern + "' " + filePath,
				Description:     "Pattern found in " + filePath,
			}
		}
		return CheckResult{
			Status:          "FAIL",
			ActualValue:     "Pattern not found",
			EvidenceCommand: "grep -Pi -- '" + pattern + "' " + filePath,
			Description:     "Pattern not found in " + filePath,
		}
	}

	if expectedResult == "not_found" {
		if !found {
			return CheckResult{
				Status:          "PASS",
				ActualValue:     "Pattern not found (as expected)",
				EvidenceCommand: "grep -Pi -- '" + pattern + "' " + filePath,
				Description:     "Pattern correctly not found in " + filePath,
			}
		}
		return CheckResult{
			Status:          "FAIL",
			ActualValue:     "Pattern found: " + truncateString(string(output), 100),
			EvidenceCommand: "grep -Pi -- '" + pattern + "' " + filePath,
			Description:     "Pattern unexpectedly found in " + filePath,
		}
	}

	return CheckResult{
		Status:          "ERROR",
		ActualValue:     "Unknown expected_result: " + expectedResult,
		EvidenceCommand: "grep -Pi -- '" + pattern + "' " + filePath,
		Description:     "Invalid expected_result value",
	}
}

func truncateString(s string, maxLen int) string {
	s = strings.TrimSpace(s)
	if len(s) <= maxLen {
		return s
	}
	return s[:maxLen-3] + "..."
}
