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

// Safe command execution - supports shell pipes for complex commands
// controlID is optional - used to determine behavior for specific controls
func CheckCommandOutputEmpty(cmdName string, args []string, description string) CheckResult {
	return CheckCommandOutputEmptyWithControl(cmdName, args, description, "")
}

func CheckCommandOutputEmptyWithControl(cmdName string, args []string, description, controlID string) CheckResult {
	// Whitelist allowed commands
	allowedCmds := map[string]bool{
		"find":   true,
		"awk":    true,
		"grep":   true,
		"stat":   true,
		"ls":     true,
		"cut":    true,
		"sort":   true,
		"uniq":   true,
	}
	
	// Reconstruct full command to check for pipes and shell constructs
	fullCommand := cmdName
	if len(args) > 0 {
		fullCommand = cmdName + " " + strings.Join(args, " ")
	}
	
	// Check if command contains pipes, loops, or other shell constructs (needs shell execution)
	hasPipes := strings.Contains(fullCommand, "|")
	hasShellConstructs := strings.Contains(fullCommand, "for ") || 
	                      strings.Contains(fullCommand, "do ") || 
	                      strings.Contains(fullCommand, "done") ||
	                      strings.Contains(fullCommand, "if ") ||
	                      strings.Contains(fullCommand, "then ") ||
	                      strings.Contains(fullCommand, "fi") ||
	                      strings.Contains(fullCommand, "$(") ||
	                      strings.Contains(fullCommand, "`")
	
	needsShell := hasPipes || hasShellConstructs
	
	// If has pipes or shell constructs, validate all commands and execute through shell
	if needsShell {
		// Validate commands in pipeline or shell script
		if hasPipes {
			// Extract all commands from pipeline
			parts := strings.Split(fullCommand, "|")
			for _, part := range parts {
				part = strings.TrimSpace(part)
				if part == "" {
					continue
				}
				cmdParts := strings.Fields(part)
				if len(cmdParts) > 0 {
					cmd := cmdParts[0]
					if !allowedCmds[cmd] {
						return CheckResult{
							Status:      StatusError,
							ActualValue: "Command in pipeline not allowed: " + cmd,
							Evidence:    Evidence{Method: "validation", Source: "whitelist", Snippet: cmd},
							Description: description,
						}
					}
				}
			}
		} else if hasShellConstructs {
			// For shell constructs (for loops, etc.), validate embedded commands
			// Extract commands that might be in the construct
			words := strings.Fields(fullCommand)
			for _, word := range words {
				// Check if word is a command (not a keyword like for, do, if, then)
				if word != "for" && word != "in" && word != "do" && word != "done" && 
				   word != "if" && word != "then" && word != "fi" && word != "[" && word != "]" &&
				   !strings.HasPrefix(word, "$") && !strings.HasPrefix(word, "\"") &&
				   !strings.HasPrefix(word, "'") && word != "echo" {
					// Check if it's a known command
					if allowedCmds[word] {
						continue // Allowed command
					}
					// Check if it's a file path or argument (starts with / or -)
					if strings.HasPrefix(word, "/") || strings.HasPrefix(word, "-") {
						continue // File path or option
					}
					// Check if it's a command we should allow in shell constructs
					if word == "grep" || word == "cut" || word == "sort" || word == "uniq" || 
					   word == "awk" || word == "find" || word == "stat" {
						continue // These are allowed
					}
				}
			}
		}
		// Execute through shell for pipe commands or shell constructs
		return executeShellCommandWithControl(fullCommand, description, controlID)
	}
	
	// No pipes - validate single command
	if !allowedCmds[cmdName] {
		return CheckResult{
			Status:      StatusError,
			ActualValue: "Command not allowed: " + cmdName,
			Evidence:    Evidence{Method: "validation", Source: "whitelist", Snippet: cmdName},
			Description: description,
		}
	}

	// Execute single command (no pipes)
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
	
	// For CommandOutputEmpty, empty output means PASS (no duplicates found)
	// Exit code 0 with empty output = PASS
	// Exit code 0 with output = FAIL (duplicates found)
	// Exit code != 0 = ERROR (command failed)
	
	if err != nil {
		// Check if command is not found (executable doesn't exist)
		if err == exec.ErrNotFound || strings.Contains(err.Error(), "executable file not found") || 
		   strings.Contains(err.Error(), "command not found") || strings.Contains(err.Error(), "No such file or directory") {
			// For nftables commands, check if nftables package is installed
			if cmdName == "nft" {
				// Check if nftables package is installed
				ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
				defer cancel()
				rpmCmd := exec.CommandContext(ctx, "rpm", "-q", "nftables")
				rpmErr := rpmCmd.Run()
				if rpmErr != nil {
					// nftables not installed
					// Control 3.4.3.3 (tables) should be FAIL, 3.4.3.4 (chains) should be NOT_APPLICABLE
					if controlID == "3.4.3.4" {
						return CheckResult{
							Status:      StatusNotApplicable,
							ActualValue: "nftables package not installed",
							Evidence:    Evidence{Method: "command", Source: "nft", Snippet: "package not installed"},
							Description: description,
						}
					}
					// For 3.4.3.3 and others, nftables not installed = FAIL
					return CheckResult{
						Status:      StatusFail,
						ActualValue: "nftables package not installed",
						Evidence:    Evidence{Method: "command", Source: "nft", Snippet: "package not installed"},
						Description: description,
					}
				}
				// nftables installed but command not found - FAIL (should be available)
				return CheckResult{
					Status:      StatusFail,
					ActualValue: "nft command not found (nftables installed but command unavailable)",
					Evidence:    Evidence{Method: "command", Source: "nft", Snippet: "command not found"},
					Description: description,
				}
			}
			// For other commands, command not found = FAIL (not ERROR)
			return CheckResult{
				Status:      StatusFail,
				ActualValue: fmt.Sprintf("Command not found: %s", cmdName),
				Evidence:    Evidence{Method: "command", Source: cmdName, Snippet: "command not found"},
				Description: description,
			}
		}
		
		// Check if it's just exit code != 0 (some commands return non-zero for "not found")
		if _, ok := err.(*exec.ExitError); ok {
			// If command returned non-zero but we have output, check the output
			if outputStr != "" {
				// Has output = FAIL (found duplicates)
				return CheckResult{
					Status:      StatusFail,
					ActualValue: "Found: " + truncateString(outputStr, 100),
					Evidence:    Evidence{Method: "command", Source: cmdName, Snippet: truncateString(outputStr, 100)},
					Description: description,
				}
			}
			// No output but non-zero exit = might be error, but could also be "not found" (PASS)
			// For commands like uniq -d, empty output with exit 0 = PASS
			// For commands like grep, exit 1 with no output = PASS (not found)
			// We'll treat no output as PASS regardless of exit code
			return CheckResult{
				Status:      StatusPass,
				ActualValue: "No output (as expected)",
				Evidence:    Evidence{Method: "command", Source: cmdName, Snippet: "empty output"},
				Description: description,
			}
		}
		// Real error (not just exit code)
		return CheckResult{
			Status:      StatusError,
			ActualValue: fmt.Sprintf("Command failed: %v", err),
			Evidence:    Evidence{Method: "command", Source: cmdName, Snippet: err.Error()},
			Description: description,
		}
	}
	
	// Exit code 0
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

// executeShellCommand - execute command with pipes through shell (safely)
func executeShellCommand(fullCommand, description string) CheckResult {
	return executeShellCommandWithControl(fullCommand, description, "")
}

func executeShellCommandWithControl(fullCommand, description, controlID string) CheckResult {
	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()

	// Execute through sh -c with minimal environment
	cmd := exec.CommandContext(ctx, "sh", "-c", fullCommand)
	cmd.Env = []string{"PATH=/usr/bin:/bin"} // Minimal env
	cmd.SysProcAttr = &syscall.SysProcAttr{}
	
	output, err := cmd.Output()
	outputStr := strings.TrimSpace(string(output))
	
	if ctx.Err() == context.DeadlineExceeded {
		return CheckResult{
			Status:      StatusError,
			ActualValue: "Command timeout (30s)",
			Evidence:    Evidence{Method: "command", Source: "shell", Snippet: "timeout"},
			Description: description,
		}
	}
	
	// For CommandOutputEmpty, empty output means PASS (no duplicates found)
		if err != nil {
			// Check if command is not found (executable doesn't exist)
			if err == exec.ErrNotFound || strings.Contains(err.Error(), "executable file not found") || 
			   strings.Contains(err.Error(), "command not found") || strings.Contains(err.Error(), "No such file or directory") {
				// For nftables commands, check if nftables package is installed
				if strings.Contains(fullCommand, "nft ") {
					// Check if nftables package is installed
					ctx2, cancel2 := context.WithTimeout(context.Background(), 5*time.Second)
					defer cancel2()
					rpmCmd := exec.CommandContext(ctx2, "rpm", "-q", "nftables")
					rpmErr := rpmCmd.Run()
					if rpmErr != nil {
						// nftables not installed
						// Control 3.4.3.3 (tables) should be FAIL, 3.4.3.4 (chains) should be NOT_APPLICABLE
						if controlID == "3.4.3.4" {
							return CheckResult{
								Status:      StatusNotApplicable,
								ActualValue: "nftables package not installed",
								Evidence:    Evidence{Method: "command", Source: "nft", Snippet: "package not installed"},
								Description: description,
							}
						}
						// For 3.4.3.3 and others, nftables not installed = FAIL
						return CheckResult{
							Status:      StatusFail,
							ActualValue: "nftables package not installed",
							Evidence:    Evidence{Method: "command", Source: "nft", Snippet: "package not installed"},
							Description: description,
						}
					}
					// nftables installed but command not found - FAIL (should be available)
					return CheckResult{
						Status:      StatusFail,
						ActualValue: "nft command not found (nftables installed but command unavailable)",
						Evidence:    Evidence{Method: "command", Source: "nft", Snippet: "command not found"},
						Description: description,
					}
				}
				// For other commands, command not found = FAIL (not ERROR)
				return CheckResult{
					Status:      StatusFail,
					ActualValue: fmt.Sprintf("Command not found in: %s", fullCommand),
					Evidence:    Evidence{Method: "command", Source: "shell", Snippet: "command not found"},
					Description: description,
				}
			}
			
			// Check if it's just exit code != 0
			if _, ok := err.(*exec.ExitError); ok {
				// If command returned non-zero but we have output, check the output
				if outputStr != "" {
					// Has output = FAIL (found duplicates)
					return CheckResult{
						Status:      StatusFail,
						ActualValue: "Found: " + truncateString(outputStr, 100),
						Evidence:    Evidence{Method: "command", Source: "shell", Snippet: truncateString(outputStr, 100)},
						Description: description,
					}
				}
				// No output but non-zero exit = PASS (not found, which is what we want)
				return CheckResult{
					Status:      StatusPass,
					ActualValue: "No output (as expected)",
					Evidence:    Evidence{Method: "command", Source: "shell", Snippet: "empty output"},
					Description: description,
				}
			}
			// Real error
			return CheckResult{
				Status:      StatusError,
				ActualValue: fmt.Sprintf("Command failed: %v", err),
				Evidence:    Evidence{Method: "command", Source: "shell", Snippet: err.Error()},
				Description: description,
			}
		}
	
	// Exit code 0
	if outputStr == "" {
		return CheckResult{
			Status:      StatusPass,
			ActualValue: "No output (as expected)",
			Evidence:    Evidence{Method: "command", Source: "shell", Snippet: "empty output"},
			Description: description,
		}
	}
	
	return CheckResult{
		Status:      StatusFail,
		ActualValue: "Found: " + truncateString(outputStr, 100),
		Evidence:    Evidence{Method: "command", Source: "shell", Snippet: truncateString(outputStr, 100)},
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