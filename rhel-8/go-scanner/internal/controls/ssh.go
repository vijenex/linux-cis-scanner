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
		return CheckResult{
			Status:          "ERROR",
			ActualValue:     err.Error(),
			EvidenceCommand: "sshd -T | grep -i " + parameter,
			Description:     description,
		}
	}

	actual, exists := config[strings.ToLower(parameter)]
	if !exists {
		return CheckResult{
			Status:          "FAIL",
			ActualValue:     "not set",
			EvidenceCommand: "sshd -T | grep -i " + parameter,
			Description:     description,
		}
	}

	status := "FAIL"
	if strings.TrimSpace(actual) == strings.TrimSpace(expected) {
		status = "PASS"
	}

	return CheckResult{
		Status:          status,
		ActualValue:     actual,
		EvidenceCommand: "sshd -T | grep -i " + parameter,
		Description:     description,
	}
}
