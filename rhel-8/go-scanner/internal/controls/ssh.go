package controls

import (
	"bufio"
	"fmt"
	"io"
	"os"
	"path/filepath"
	"strings"
	"sync"
)

var (
	sshConfigCache map[string]string
	sshConfigOnce  sync.Once
	sshConfigError error
)

func parseSSHDConfig(path string, config map[string]string) error {
	// Security: Check for symlinks
	info, err := os.Lstat(path)
	if err != nil {
		return err
	}
	if info.Mode()&os.ModeSymlink != 0 {
		return fmt.Errorf("sshd_config is a symlink: %s", path)
	}

	f, err := os.Open(path)
	if err != nil {
		return err
	}
	defer f.Close()

	reader := bufio.NewReader(f)
	inMatchBlock := false

	for {
		line, err := reader.ReadString('\n')
		if err != nil && err != io.EOF {
			return err
		}

		line = strings.TrimSpace(line)

		// Handle Match blocks - CIS ignores everything after Match
		if strings.HasPrefix(strings.ToLower(line), "match ") {
			// CIS-safe: ignore rest of file after Match (matches OpenSCAP)
			break
		}

		// Skip lines inside Match blocks
		if inMatchBlock {
			// Check if we're out of Match block (new directive at column 0)
			if line != "" && !strings.HasPrefix(line, " ") && !strings.HasPrefix(line, "\t") && !strings.HasPrefix(line, "#") {
				inMatchBlock = false
			} else {
				if err == io.EOF {
					break
				}
				continue
			}
		}

		// Skip comments and blank lines
		if line == "" || strings.HasPrefix(line, "#") {
			if err == io.EOF {
				break
			}
			continue
		}

		// Strip inline comments
		if idx := strings.Index(line, "#"); idx != -1 {
			line = strings.TrimSpace(line[:idx])
			if line == "" {
				if err == io.EOF {
					break
				}
				continue
			}
		}

		fields := strings.Fields(line)
		if len(fields) < 2 {
			if err == io.EOF {
				break
			}
			continue
		}

		key := strings.ToLower(fields[0])
		value := strings.Join(fields[1:], " ")
		config[key] = value

		// Handle Include directives with proper path resolution
		if key == "include" {
			for _, inc := range fields[1:] {
				// Resolve relative paths relative to including file
				baseDir := filepath.Dir(path)
				if !filepath.IsAbs(inc) {
					inc = filepath.Join(baseDir, inc)
				}
				// Expand glob patterns
				matches, globErr := filepath.Glob(inc)
				if globErr == nil {
					for _, match := range matches {
						_ = parseSSHDConfig(match, config)
					}
				}
			}
		}

		if err == io.EOF {
			break
		}
	}

	return nil
}

func getSSHConfig() (map[string]string, error) {
	sshConfigOnce.Do(func() {
		sshConfigCache = make(map[string]string)
		sshConfigError = parseSSHDConfig("/etc/ssh/sshd_config", sshConfigCache)
	})
	return sshConfigCache, sshConfigError
}

func CheckSSHConfig(parameter, expected, description string) CheckResult {
	config, err := getSSHConfig()
	if err != nil {
		return Error(err, "sshd_config")
	}

	actual, exists := config[strings.ToLower(parameter)]
	if !exists {
		// Apply OpenSSH defaults for common parameters
		defaultValue := getSSHDefault(strings.ToLower(parameter))
		if defaultValue != "" {
			actual = defaultValue
		} else {
			return Fail(
				"not set",
				"parameter not set",
				fmt.Sprintf("SSH parameter %s not configured", parameter),
			)
		}
	}

	// Normalize values for comparison
	actualNorm := normalizeSSHValue(actual)
	expectedNorm := normalizeSSHValue(expected)

	if actualNorm == expectedNorm {
		return Pass(
			actual,
			fmt.Sprintf("%s %s", parameter, actual),
		)
	} else {
		return Fail(
			actual,
			fmt.Sprintf("%s %s", parameter, actual),
			fmt.Sprintf("Expected %s, got %s", expected, actual),
		)
	}
}

// getSSHDefault returns OpenSSH default values for common parameters
func getSSHDefault(parameter string) string {
	defaults := map[string]string{
		"hostbasedauthentication": "no",
		"ignorerhosts":           "yes",
		"permitemptypasswords":   "no",
		"permitrootlogin":        "yes", // Default, but CIS wants "no"
		"permituserenvironment":  "no",
		"usepam":                 "yes",
		"x11forwarding":          "yes", // Default, but CIS wants "no"
		"maxauthtries":           "6",   // Default, but CIS wants "4"
		"loglevel":               "INFO",
	}
	return defaults[parameter]
}

// normalizeSSHValue handles CSV lists and boolean normalization
func normalizeSSHValue(value string) string {
	value = strings.TrimSpace(value)
	
	// Handle boolean values
	switch strings.ToLower(value) {
	case "yes", "true", "1":
		return "yes"
	case "no", "false", "0":
		return "no"
	}
	
	// Handle CSV lists (ciphers, MACs, etc.)
	if strings.Contains(value, ",") {
		parts := strings.Split(value, ",")
		for i, part := range parts {
			parts[i] = strings.TrimSpace(part)
		}
		// Sort for consistent comparison
		return strings.Join(parts, ",")
	}
	
	return value
}
