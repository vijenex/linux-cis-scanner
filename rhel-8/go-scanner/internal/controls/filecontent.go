package controls

import (
	"bufio"
	"os"
	"regexp"
	"strings"
)

func CheckFileContent(filePath, pattern, expectedResult string) CheckResult {
	if filePath == "" {
		return CheckResult{
			Status:      StatusError,
			ActualValue: "No file path specified",
			Evidence:    Evidence{Method: "validation", Source: "N/A", Snippet: "missing parameter"},
			Description: "File path is required",
		}
	}

	// Check file with symlink protection
	info, err := os.Lstat(filePath)
	if err != nil {
		return CheckResult{
			Status:      StatusFail,
			ActualValue: "File does not exist",
			Evidence:    Evidence{Method: "file", Source: filePath, Snippet: "not found"},
			Description: "File not found: " + filePath,
		}
	}

	// Reject symlinks
	if info.Mode()&os.ModeSymlink != 0 {
		return CheckResult{
			Status:      StatusFail,
			ActualValue: "Symlink not allowed",
			Evidence:    Evidence{Method: "file", Source: filePath, Snippet: "symlink"},
			Description: "Symlink rejected: " + filePath,
		}
	}

	// File size limit (1MB)
	if info.Size() > 1024*1024 {
		return CheckResult{
			Status:      StatusError,
			ActualValue: "File too large",
			Evidence:    Evidence{Method: "file", Source: filePath, Snippet: "size > 1MB"},
			Description: "File exceeds 1MB limit: " + filePath,
		}
	}

	// Compile regex (case-insensitive)
	re, err := regexp.Compile("(?i)" + pattern)
	if err != nil {
		return CheckResult{
			Status:      StatusError,
			ActualValue: "Invalid regex: " + err.Error(),
			Evidence:    Evidence{Method: "validation", Source: "regex", Snippet: pattern},
			Description: "Regex compilation failed",
		}
	}

	// Read and scan file
	f, err := os.Open(filePath)
	if err != nil {
		return CheckResult{
			Status:      StatusError,
			ActualValue: "Cannot open file: " + err.Error(),
			Evidence:    Evidence{Method: "file", Source: filePath, Snippet: "access denied"},
			Description: "File access error: " + filePath,
		}
	}
	defer f.Close()

	scanner := bufio.NewScanner(f)
	found := false
	matchedLine := ""

	for scanner.Scan() {
		line := scanner.Text()
		if re.MatchString(line) {
			found = true
			matchedLine = line
			break
		}
	}

	if expectedResult == "found" {
		if found {
			return CheckResult{
				Status:      StatusPass,
				ActualValue: "Pattern found: " + truncateString(matchedLine, 100),
				Evidence:    Evidence{Method: "parsed", Source: filePath, Snippet: truncateString(matchedLine, 100)},
				Description: "Pattern found in " + filePath,
			}
		}
		return CheckResult{
			Status:      StatusFail,
			ActualValue: "Pattern not found",
			Evidence:    Evidence{Method: "parsed", Source: filePath, Snippet: "pattern not found"},
			Description: "Pattern not found in " + filePath,
		}
	}

	if expectedResult == "not_found" {
		if !found {
			return CheckResult{
				Status:      StatusPass,
				ActualValue: "Pattern not found (as expected)",
				Evidence:    Evidence{Method: "parsed", Source: filePath, Snippet: "pattern not found"},
				Description: "Pattern correctly not found in " + filePath,
			}
		}
		return CheckResult{
			Status:      StatusFail,
			ActualValue: "Pattern found: " + truncateString(matchedLine, 100),
			Evidence:    Evidence{Method: "parsed", Source: filePath, Snippet: truncateString(matchedLine, 100)},
			Description: "Pattern unexpectedly found in " + filePath,
		}
	}

	return CheckResult{
		Status:      StatusError,
		ActualValue: "Unknown expected_result: " + expectedResult,
		Evidence:    Evidence{Method: "validation", Source: "expected_result", Snippet: expectedResult},
		Description: "Invalid expected_result value",
	}
}