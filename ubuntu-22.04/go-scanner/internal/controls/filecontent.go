package controls

import (
	"bufio"
	"fmt"
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

	// Support multiple files (space-separated or comma-separated)
	// This allows controls like 4.5.1.1 to check both /etc/pam.d/password-auth and /etc/pam.d/system-auth
	filePaths := []string{}
	if strings.Contains(filePath, " ") {
		filePaths = strings.Fields(filePath)
	} else if strings.Contains(filePath, ",") {
		filePaths = strings.Split(filePath, ",")
		for i := range filePaths {
			filePaths[i] = strings.TrimSpace(filePaths[i])
		}
	} else {
		filePaths = []string{filePath}
	}

	// Check all files - for "found", at least one must match; for "not_found", all must not match
	var allResults []CheckResult
	var foundCount int
	var checkedFiles []string

	for _, fp := range filePaths {
		// Check file with symlink protection
		info, err := os.Lstat(fp)
		if err != nil {
			// For optional service configs (like postfix), missing file = NOT_APPLICABLE
			if strings.Contains(fp, "postfix") || strings.Contains(fp, "sendmail") || 
			   strings.Contains(fp, "exim") || strings.Contains(fp, "qmail") {
				// MTA not installed - NOT_APPLICABLE
				return CheckResult{
					Status:      StatusNotApplicable,
					ActualValue: fmt.Sprintf("MTA not installed (file %s does not exist)", fp),
					Evidence:    Evidence{Method: "file", Source: fp, Snippet: "service not installed"},
					Description: fmt.Sprintf("Mail Transfer Agent not installed: %s", fp),
				}
			}
			// If file doesn't exist and we're looking for "found", it's a fail
			if expectedResult == "found" {
				allResults = append(allResults, CheckResult{
					Status:      StatusFail,
					ActualValue: "File does not exist: " + fp,
					Evidence:    Evidence{Method: "file", Source: fp, Snippet: "not found"},
					Description: "File not found: " + fp,
				})
			}
			// For "not_found", missing file is OK (pattern not found)
			continue
		}

		// Reject symlinks
		if info.Mode()&os.ModeSymlink != 0 {
			allResults = append(allResults, CheckResult{
				Status:      StatusFail,
				ActualValue: "Symlink not allowed: " + fp,
				Evidence:    Evidence{Method: "file", Source: fp, Snippet: "symlink"},
				Description: "Symlink rejected: " + fp,
			})
			continue
		}

		// File size limit (1MB)
		if info.Size() > 1024*1024 {
			allResults = append(allResults, CheckResult{
				Status:      StatusError,
				ActualValue: "File too large: " + fp,
				Evidence:    Evidence{Method: "file", Source: fp, Snippet: "size > 1MB"},
				Description: "File exceeds 1MB limit: " + fp,
			})
			continue
		}

		checkedFiles = append(checkedFiles, fp)
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

	// Check all files
	var matchedLines []string
	for _, fp := range checkedFiles {
		// Read and scan file
		f, err := os.Open(fp)
		if err != nil {
			allResults = append(allResults, CheckResult{
				Status:      StatusError,
				ActualValue: "Cannot open file: " + err.Error(),
				Evidence:    Evidence{Method: "file", Source: fp, Snippet: "access denied"},
				Description: "File access error: " + fp,
			})
			continue
		}

		scanner := bufio.NewScanner(f)
		for scanner.Scan() {
			line := scanner.Text()
			if re.MatchString(line) {
				foundCount++
				matchedLines = append(matchedLines, fp+": "+truncateString(line, 80))
				break // Found in this file, move to next
			}
		}
		f.Close()
	}

	// Evaluate results based on expectedResult
	if expectedResult == "found" {
		// For "found", at least one file must contain the pattern
		if foundCount > 0 {
			return CheckResult{
				Status:      StatusPass,
				ActualValue: fmt.Sprintf("Pattern found in %d file(s): %s", foundCount, strings.Join(matchedLines, "; ")),
				Evidence:    Evidence{Method: "parsed", Source: strings.Join(checkedFiles, ", "), Snippet: strings.Join(matchedLines, "; ")},
				Description: fmt.Sprintf("Pattern found in %s", strings.Join(checkedFiles, ", ")),
			}
		}
		// If we had errors, return first error; otherwise pattern not found
		if len(allResults) > 0 {
			return allResults[0]
		}
		return CheckResult{
			Status:      StatusFail,
			ActualValue: "Pattern not found in any file",
			Evidence:    Evidence{Method: "parsed", Source: strings.Join(checkedFiles, ", "), Snippet: "pattern not found"},
			Description: "Pattern not found in " + strings.Join(checkedFiles, ", "),
		}
	}

	if expectedResult == "not_found" {
		// For "not_found", pattern must not be in ANY file
		if foundCount == 0 {
			return CheckResult{
				Status:      StatusPass,
				ActualValue: "Pattern not found in any file (as expected)",
				Evidence:    Evidence{Method: "parsed", Source: strings.Join(checkedFiles, ", "), Snippet: "pattern not found"},
				Description: "Pattern correctly not found in " + strings.Join(checkedFiles, ", "),
			}
		}
		return CheckResult{
			Status:      StatusFail,
			ActualValue: fmt.Sprintf("Pattern found in %d file(s): %s", foundCount, strings.Join(matchedLines, "; ")),
			Evidence:    Evidence{Method: "parsed", Source: strings.Join(checkedFiles, ", "), Snippet: strings.Join(matchedLines, "; ")},
			Description: "Pattern unexpectedly found in " + strings.Join(checkedFiles, ", "),
		}
	}

	return CheckResult{
		Status:      StatusError,
		ActualValue: "Unknown expected_result: " + expectedResult,
		Evidence:    Evidence{Method: "validation", Source: "expected_result", Snippet: expectedResult},
		Description: "Invalid expected_result value",
	}
}