package controls

import (
	"context"
	"fmt"
	"os"
	"os/exec"
	"strings"
	"syscall"
	"time"
)

// Safe command execution - no shell, structured args only
func CheckCommandOutputEmpty(cmdName string, args []string, description string) CheckResult {
	// Whitelist allowed commands
	allowedCmds := map[string]bool{
		"find":   true,
		"awk":    true,
		"grep":   true,
		"stat":   true,
		"ls":     true,
	}
	
	if !allowedCmds[cmdName] {
		return CheckResult{
			Status:      StatusError,
			ActualValue: "Command not allowed: " + cmdName,
			Evidence:    Evidence{Method: "validation", Source: "whitelist", Snippet: cmdName},
			Description: description,
		}
	}

	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()

	cmd := exec.CommandContext(ctx, cmdName, args...)
	cmd.Env = []string{"PATH=/usr/bin:/bin"} // Minimal env
	cmd.SysProcAttr = &syscall.SysProcAttr{}
	
	output, err := cmd.Output()
	outputStr := strings.TrimSpace(string(output))
	
	if ctx.Err() == context.DeadlineExceeded {
		return CheckResult{
			Status:      StatusError,
			ActualValue: "Command timeout (30s)",
			Evidence:    Evidence{Method: "command", Source: cmdName, Snippet: "timeout"},
			Description: description,
		}
	}
	
	if err != nil && outputStr == "" {
		return CheckResult{
			Status:      StatusError,
			ActualValue: fmt.Sprintf("Command failed: %v", err),
			Evidence:    Evidence{Method: "command", Source: cmdName, Snippet: err.Error()},
			Description: description,
		}
	}
	
	if outputStr == "" {
		return CheckResult{
			Status:      StatusPass,
			ActualValue: "No output (as expected)",
			Evidence:    Evidence{Method: "command", Source: cmdName, Snippet: "empty output"},
			Description: description,
		}
	}
	
	return CheckResult{
		Status:      StatusFail,
		ActualValue: "Found: " + truncateString(outputStr, 100),
		Evidence:    Evidence{Method: "command", Source: cmdName, Snippet: truncateString(outputStr, 100)},
		Description: description,
	}
}

func CheckFileExists(filePath, description string) CheckResult {
	info, err := os.Lstat(filePath)
	if err != nil {
		return CheckResult{
			Status:      StatusFail,
			ActualValue: "File does not exist",
			Evidence:    Evidence{Method: "file", Source: filePath, Snippet: "not found"},
			Description: description,
		}
	}

	// Reject symlinks for security
	if info.Mode()&os.ModeSymlink != 0 {
		return CheckResult{
			Status:      StatusFail,
			ActualValue: "Symlink not allowed",
			Evidence:    Evidence{Method: "file", Source: filePath, Snippet: "symlink"},
			Description: description,
		}
	}

	if info.Mode().IsRegular() {
		return CheckResult{
			Status:      StatusPass,
			ActualValue: fmt.Sprintf("File exists (size: %d bytes)", info.Size()),
			Evidence:    Evidence{Method: "file", Source: filePath, Snippet: fmt.Sprintf("size: %d", info.Size())},
			Description: description,
		}
	}

	return CheckResult{
		Status:      StatusFail,
		ActualValue: fmt.Sprintf("Not a regular file (mode: %s)", info.Mode()),
		Evidence:    Evidence{Method: "file", Source: filePath, Snippet: info.Mode().String()},
		Description: description,
	}
}

func truncateString(s string, maxLen int) string {
	s = strings.TrimSpace(s)
	if len(s) <= maxLen {
		return s
	}
	return s[:maxLen-3] + "..."
}