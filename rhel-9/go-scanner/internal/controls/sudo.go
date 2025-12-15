package controls

import (
	"bufio"
	"fmt"
	"io"
	"os"
	"path/filepath"
	"sort"
	"strings"
	"sync"
)

type SudoDefaults struct {
	Key        string
	Value      string // empty for flags
	Negated    bool
	SourceFile string
}

var (
	sudoDefaultsCache []SudoDefaults
	sudoDefaultsOnce  sync.Once
	sudoDefaultsError error
)

func parseSudoers(path string, results *[]SudoDefaults) error {
	// Security: Check for symlinks
	info, err := os.Lstat(path)
	if err != nil {
		return err
	}
	if info.Mode()&os.ModeSymlink != 0 {
		return fmt.Errorf("sudoers is symlink: %s", path)
	}

	f, err := os.Open(path)
	if err != nil {
		return err
	}
	defer f.Close()

	reader := bufio.NewReader(f)

	for {
		line, err := reader.ReadString('\n')
		if err != nil && err != io.EOF {
			return err
		}

		// Strip inline comments
		if idx := strings.Index(line, "#"); idx != -1 {
			// Check if this is an include directive
			if strings.HasPrefix(strings.TrimSpace(line), "#includedir") {
				// Handle includedir
				parts := strings.Fields(strings.TrimSpace(line))
				if len(parts) == 2 {
					files, dirErr := os.ReadDir(parts[1])
					if dirErr == nil {
						// Sort files lexicographically per sudoers semantics
						sort.Slice(files, func(i, j int) bool {
							return files[i].Name() < files[j].Name()
						})
						for _, f := range files {
							if !f.IsDir() && !strings.HasPrefix(f.Name(), ".") && strings.HasSuffix(f.Name(), ".conf") {
								_ = parseSudoers(filepath.Join(parts[1], f.Name()), results)
							}
						}
					}
				}
			} else {
				// Regular comment, strip it
				line = line[:idx]
			}
		}

		line = strings.TrimSpace(line)
		if line == "" {
			if err == io.EOF {
				break
			}
			continue
		}

		// Only process Defaults lines
		if !strings.HasPrefix(line, "Defaults") {
			if err == io.EOF {
				break
			}
			continue
		}

		fields := strings.Fields(line)
		if len(fields) < 2 {
			if err == io.EOF {
				break
			}
			continue
		}

		// Only global Defaults (no colon or @ for scoped defaults)
		if strings.Contains(fields[0], ":") || strings.Contains(fields[0], "@") {
			if err == io.EOF {
				break
			}
			continue
		}

		// Parse each default setting
		for _, field := range fields[1:] {
			d := SudoDefaults{SourceFile: path}

			// Handle negation
			if strings.HasPrefix(field, "!") {
				d.Negated = true
				field = strings.TrimPrefix(field, "!")
			}

			// Handle key=value pairs
			if strings.Contains(field, "=") {
				kv := strings.SplitN(field, "=", 2)
				if len(kv) == 2 {
					d.Key = kv[0]
					// Remove quotes from value
					d.Value = strings.Trim(kv[1], `"`)
				}
			} else {
				// Handle flags
				d.Key = field
				d.Value = "enabled"
			}

			*results = append(*results, d)
		}

		if err == io.EOF {
			break
		}
	}

	return nil
}

func getSudoDefaults() ([]SudoDefaults, error) {
	sudoDefaultsOnce.Do(func() {
		sudoDefaultsCache = []SudoDefaults{}
		sudoDefaultsError = parseSudoers("/etc/sudoers", &sudoDefaultsCache)
	})
	return sudoDefaultsCache, sudoDefaultsError
}

func checkSudoDefault(defaults []SudoDefaults, key, expected string) (string, bool) {
	// Last match wins (iterate backwards)
	for i := len(defaults) - 1; i >= 0; i-- {
		if defaults[i].Key == key {
			if defaults[i].Negated {
				return "disabled", true
			}
			return defaults[i].Value, true
		}
	}
	return "", false
}

func CheckSudoConfig(parameter, expected, description string) CheckResult {
	defaults, err := getSudoDefaults()
	if err != nil {
		return CheckResult{
			Status:          "ERROR",
			ActualValue:     err.Error(),
			EvidenceCommand: "sudo -l -U root",
			Description:     description,
		}
	}

	actual, found := checkSudoDefault(defaults, parameter, expected)
	if !found {
		return CheckResult{
			Status:          "FAIL",
			ActualValue:     "not set",
			EvidenceCommand: "sudo -l -U root",
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
		EvidenceCommand: "sudo -l -U root",
		Description:     description,
	}
}
