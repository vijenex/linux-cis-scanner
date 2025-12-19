package controls

import (
	"bufio"
	"fmt"
	"io"
	"os"
	"path/filepath"
	"strings"
)

type PAMEntry struct {
	Type      string            // auth, account, password, session
	Control   string            // required, requisite, sufficient, optional
	Module    string            // pam_pwquality.so
	Arguments map[string]string // key=value pairs
	RawLine   string            // original line for debugging
}

func parsePAMFile(path string) ([]PAMEntry, error) {
	// Security: Check for symlinks
	info, err := os.Lstat(path)
	if err != nil {
		return nil, err
	}
	if info.Mode()&os.ModeSymlink != 0 {
		return nil, fmt.Errorf("PAM file is a symlink: %s", path)
	}

	f, err := os.Open(path)
	if err != nil {
		return nil, err
	}
	defer f.Close()

	reader := bufio.NewReader(f)
	var entries []PAMEntry

	for {
		line, err := reader.ReadString('\n')
		if err != nil && err != io.EOF {
			return nil, err
		}

		originalLine := line

		// Strip comments
		if idx := strings.Index(line, "#"); idx != -1 {
			line = line[:idx]
		}

		line = strings.TrimSpace(line)
		if line == "" {
			if err == io.EOF {
				break
			}
			continue
		}

		// Handle @include directives
		if strings.HasPrefix(line, "@include") {
			fields := strings.Fields(line)
			if len(fields) >= 2 {
				includePath := fields[1]
				if !strings.HasPrefix(includePath, "/") {
					includePath = "/etc/pam.d/" + includePath
				}
				includeEntries, _ := parsePAMFile(includePath)
				entries = append(entries, includeEntries...)
			}
			if err == io.EOF {
				break
			}
			continue
		}

		fields := strings.Fields(line)
		if len(fields) < 3 {
			if err == io.EOF {
				break
			}
			continue
		}

		// Handle substack
		if fields[1] == "substack" {
			substackPath := fields[2]
			if !strings.HasPrefix(substackPath, "/") {
				substackPath = "/etc/pam.d/" + substackPath
			}
			substackEntries, _ := parsePAMFile(substackPath)
			// Filter substack entries to match the current type
			for _, se := range substackEntries {
				if se.Type == fields[0] {
					entries = append(entries, se)
				}
			}
			if err == io.EOF {
				break
			}
			continue
		}

		entry := PAMEntry{
			Type:      fields[0],
			Control:   fields[1],
			Module:    filepath.Base(fields[2]), // Extract just the module name
			Arguments: make(map[string]string),
			RawLine:   strings.TrimSpace(originalLine),
		}

		// Parse arguments (key=value pairs)
		for _, arg := range fields[3:] {
			if strings.Contains(arg, "=") {
				kv := strings.SplitN(arg, "=", 2)
				if len(kv) == 2 {
					// Strip quotes from values
					value := strings.Trim(kv[1], `"`)
					entry.Arguments[kv[0]] = value
				}
			} else {
				// Handle flags without values
				entry.Arguments[arg] = ""
			}
		}

		entries = append(entries, entry)

		if err == io.EOF {
			break
		}
	}

	return entries, nil
}

func checkPAMParameter(entries []PAMEntry, pamType, module, parameter, expected string) (string, bool) {
	// Look for the parameter in matching entries (last match wins for most cases)
	var lastValue string
	found := false

	for _, entry := range entries {
		// Match PAM type (if specified)
		if pamType != "" && entry.Type != pamType {
			continue
		}

		// Exact module match
		if entry.Module != module {
			continue
		}

		// Check if parameter exists
		if val, exists := entry.Arguments[parameter]; exists {
			lastValue = val
			found = true
		}
	}

	return lastValue, found
}

func CheckPAMConfig(filePath, module, parameter, expected, description string) CheckResult {
	entries, err := parsePAMFile(filePath)
	if err != nil {
		return CheckResult{
			Status:          "ERROR",
			ActualValue:     err.Error(),
			EvidenceCommand: fmt.Sprintf("cat %s", filePath),
			Description:     description,
		}
	}

	// Check for the parameter (no PAM type filter for backward compatibility)
	actual, found := checkPAMParameter(entries, "", module, parameter, expected)

	if !found {
		return CheckResult{
			Status:          "FAIL",
			ActualValue:     "parameter not found",
			EvidenceCommand: fmt.Sprintf("grep %s %s", module, filePath),
			Description:     description,
		}
	}

	status := "FAIL"
	if actual == expected {
		status = "PASS"
	}

	return CheckResult{
		Status:          Status(status),
		ActualValue:     actual,
		EvidenceCommand: fmt.Sprintf("grep %s %s", module, filePath),
		Description:     description,
	}
}
