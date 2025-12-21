package scanner

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"strings"

	"github.com/vijenex/linux-cis-scanner/ubuntu-22.04/internal/controls"
	"github.com/vijenex/linux-cis-scanner/ubuntu-22.04/internal/report"
)

type Scanner struct {
	OutputDir  string
	Profile    string
	Milestones []Milestone
}

type Milestone struct {
	ID          string                    `json:"milestone"`
	Section     string                    `json:"section"`
	Description string                    `json:"description"`
	Controls    []controls.LegacyControl `json:"controls"`
}

type Result struct {
	ID              string
	Title           string
	Section         string
	Status          string
	CISReference    string
	Remediation     string
	Description     string
	ActualValue     string
	EvidenceCommand string
}

func NewScanner(outputDir, profile string) *Scanner {
	return &Scanner{
		OutputDir: outputDir,
		Profile:   profile,
	}
}

func (s *Scanner) LoadMilestones(milestoneFiles []string) error {
	// Create output directory
	if err := os.MkdirAll(s.OutputDir, 0755); err != nil {
		return fmt.Errorf("failed to create output directory: %w", err)
	}

	// Get milestone directory - use milestones with 234 automated controls
	milestonesDir := "milestones"
	// If running from go-scanner dir, go up one level
	if _, err := os.Stat(milestonesDir); os.IsNotExist(err) {
		milestonesDir = filepath.Join("..", "milestones")
		// Verify fallback path exists
		if _, err := os.Stat(milestonesDir); os.IsNotExist(err) {
			return fmt.Errorf("milestone directory not found: tried 'milestones' and '../milestones'")
		}
	}

	// If no specific milestones provided, load all
	if len(milestoneFiles) == 0 {
		files, err := filepath.Glob(filepath.Join(milestonesDir, "milestone-*.json"))
		if err != nil {
			return fmt.Errorf("failed to list milestone files: %w", err)
		}
		for _, f := range files {
			milestoneFiles = append(milestoneFiles, filepath.Base(f))
		}
	}

	// Load each milestone
	for _, filename := range milestoneFiles {
		path := filepath.Join(milestonesDir, filename)
		data, err := os.ReadFile(path)
		if err != nil {
			return fmt.Errorf("failed to read %s: %w", filename, err)
		}

		var milestone Milestone
		if err := json.Unmarshal(data, &milestone); err != nil {
			return fmt.Errorf("failed to parse %s: %w", filename, err)
		}

		s.Milestones = append(s.Milestones, milestone)
	}

	return nil
}

func (s *Scanner) ExecuteControls() []Result {
	var results []Result

	// Build ScanContext once for entire scan
	fmt.Printf("🔍 Building scan context...\n")
	scanCtx, err := controls.BuildScanContext()
	if err != nil {
		fmt.Printf("❌ Failed to build scan context: %v\n", err)
		return results
	}
	fmt.Printf("✅ Scan context built (Host: %s, OS: %s)\n", scanCtx.Meta.Hostname, scanCtx.Meta.OSName)

	for _, milestone := range s.Milestones {
		fmt.Printf("📄 Processing %s...\n", milestone.ID)

		for _, ctrl := range milestone.Controls {
			// Always exclude Level 2 controls (as per requirement)
			if ctrl.Profile == "Level2" {
				// Skip Level 2 controls completely - don't add to results
				continue
			}
			
			// Determine if control is automated
			// Logic: 
			// 1. If type is "Manual", always manual
			// 2. If automated field is explicitly set to false, manual
			// 3. If automated field is missing or true, automated (default to automated)
			isAutomated := false
			
			// Debug: Log first few controls to verify parsing
			if len(results) < 3 {
				automatedStr := "nil"
				if ctrl.Automated != nil {
					automatedStr = fmt.Sprintf("%v", *ctrl.Automated)
				}
				fmt.Printf("  [DEBUG] %s: type=%s, automated=%s\n", ctrl.ID, ctrl.Type, automatedStr)
			}
			
			if ctrl.Type == "Manual" {
				// Explicitly manual type - always manual
				isAutomated = false
			} else if ctrl.Automated != nil && *ctrl.Automated == false {
				// Explicitly set to false - manual
				isAutomated = false
			} else {
				// automated field is missing (nil) or explicitly true
				// Default to automated (most control types are automated)
				isAutomated = true
			}
			
			// Skip non-automated controls
			if !isAutomated {
				results = append(results, Result{
					ID:          ctrl.ID,
					Title:       ctrl.Title,
					Section:     ctrl.Section,
					Status:      "MANUAL",
					CISReference: ctrl.CISReference,
					Remediation: ctrl.Remediation,
					Description: "Manual verification required per CIS",
				})
				continue
			}

			// Normalize and validate control
			ctrl.Normalize()
			if err := ctrl.Validate(); err != nil {
				results = append(results, Result{
					ID:          ctrl.ID,
					Title:       ctrl.Title,
					Section:     ctrl.Section,
					Status:      "ERROR",
					CISReference: ctrl.CISReference,
					Remediation: ctrl.Remediation,
					Description: fmt.Sprintf("Validation failed: %v", err),
				})
				continue
			}
			
			// Execute control with context
			result := s.executeControlWithContext(scanCtx, ctrl)
			// Normalize status to eliminate SKIPPED and handle legacy
			result.Status = NormalizeStatus(result.Status)
			results = append(results, result)

			// Print status
			statusSymbol := getStatusSymbol(result.Status)
			fmt.Printf("  %s %s: %s\n", statusSymbol, ctrl.ID, truncate(ctrl.Title, 60))
		}
	}

	return results
}

func (s *Scanner) executeControlWithContext(scanCtx *controls.ScanContext, ctrl controls.LegacyControl) Result {
	result := Result{
		ID:           ctrl.ID,
		Title:        ctrl.Title,
		Section:      ctrl.Section,
		CISReference: ctrl.CISReference,
		Remediation:  ctrl.Remediation,
		Description:  ctrl.Description,
	}

	// Execute based on control type using ScanContext
	switch ctrl.Type {
	case "SysctlParameter":
		// Use new context-aware sysctl check
		paramName := ctrl.ParameterName
		if paramName == "" {
			paramName = ctrl.Parameter
		}
		checkResult := controls.CheckSysctlWithContext(scanCtx, paramName, ctrl.ExpectedValue)
		result.Status = string(checkResult.Status)
		result.ActualValue = checkResult.ActualValue
		result.EvidenceCommand = checkResult.Evidence.Source + ": " + checkResult.Evidence.Snippet

	default:
		// Fall back to legacy execution for other types
		return s.executeControl(ctrl)
	}

	return result
}

func (s *Scanner) executeControl(ctrl controls.LegacyControl) Result {
	result := Result{
		ID:           ctrl.ID,
		Title:        ctrl.Title,
		Section:      ctrl.Section,
		CISReference: ctrl.CISReference,
		Remediation:  ctrl.Remediation,
		Description:  ctrl.Description,
	}

	// Execute based on control type
	switch ctrl.Type {
	case "KernelModule":
		checkResult := controls.CheckKernelModule(ctrl.ModuleName, ctrl.ExpectedStatus)
		result.Status = string(checkResult.Status)
		result.ActualValue = checkResult.ActualValue
		result.EvidenceCommand = checkResult.EvidenceCommand
		// Keep original CIS description, don't overwrite

	case "MountPoint":
		checkResult := controls.CheckMountPoint(ctrl.MountPoint, ctrl.ExpectedStatus)
		result.Status = string(checkResult.Status)
		result.ActualValue = checkResult.ActualValue
		result.EvidenceCommand = checkResult.EvidenceCommand

	case "MountOption":
		checkResult := controls.CheckMountOption(ctrl.MountPoint, ctrl.RequiredOption)
		result.Status = string(checkResult.Status)
		result.ActualValue = checkResult.ActualValue
		result.EvidenceCommand = checkResult.EvidenceCommand

	case "ServiceStatus", "Service", "ServiceNotInUse":
		// Handle service checks - ServiceNotInUse expects "disabled" or "inactive"
		// ServiceNotInUse may have service_names array - use first one
		serviceName := ctrl.ServiceName
		if serviceName == "" && len(ctrl.ServiceNames) > 0 {
			serviceName = ctrl.ServiceNames[0]
		}
		expectedStatus := ctrl.ExpectedStatus
		if expectedStatus == "" && ctrl.Type == "ServiceNotInUse" {
			expectedStatus = "disabled"
		}
		if serviceName == "" {
			result.Status = "ERROR"
			result.ActualValue = "Missing service_name or service_names"
			result.EvidenceCommand = "N/A"
		} else {
			checkResult := controls.CheckServiceStatus(serviceName, expectedStatus)
			result.Status = string(checkResult.Status)
			result.ActualValue = checkResult.ActualValue
			result.EvidenceCommand = checkResult.EvidenceCommand
		}

	case "PackageInstalled", "Package", "MultiPackage":
		// Handle package checks - default to "installed" if not specified
		// Package may use "package" field or "package_names" array
		packageName := ctrl.PackageName
		if packageName == "" && ctrl.Package != "" {
			packageName = ctrl.Package
		}
		if packageName == "" && len(ctrl.PackageNames) > 0 {
			packageName = ctrl.PackageNames[0]
		}
		expectedStatus := ctrl.ExpectedStatus
		if expectedStatus == "" && ctrl.ExpectedState != "" {
			expectedStatus = ctrl.ExpectedState
		}
		if expectedStatus == "" && ctrl.ShouldBeInstalled != nil {
			if *ctrl.ShouldBeInstalled {
				expectedStatus = "installed"
			} else {
				expectedStatus = "not_installed"
			}
		}
		if expectedStatus == "" {
			expectedStatus = "installed"
		}
		if packageName == "" {
			result.Status = "ERROR"
			result.ActualValue = "Missing package_name, package, or package_names"
			result.EvidenceCommand = "N/A"
		} else {
			checkResult := controls.CheckPackageInstalled(packageName, expectedStatus)
			result.Status = string(checkResult.Status)
			result.ActualValue = checkResult.ActualValue
			result.EvidenceCommand = checkResult.EvidenceCommand
		}

	case "PackageNotInstalled":
		checkResult := controls.CheckPackageInstalled(ctrl.PackageName, "not_installed")
		result.Status = string(checkResult.Status)
		result.ActualValue = checkResult.ActualValue
		result.EvidenceCommand = checkResult.EvidenceCommand

	case "SysctlParameter", "KernelParameter":
		// Support both parameter_name and parameter fields
		paramName := ctrl.ParameterName
		if paramName == "" {
			paramName = ctrl.Parameter
		}
		checkResult := controls.CheckSysctlParameter(paramName, ctrl.ExpectedValue)
		result.Status = string(checkResult.Status)
		result.ActualValue = checkResult.ActualValue
		result.EvidenceCommand = checkResult.EvidenceCommand

	case "MultiKernelParameter":
		// MultiKernelParameter has a parameters array - check each one
		// If any fails, the whole control fails
		if len(ctrl.ParametersArray) == 0 {
			result.Status = "ERROR"
			result.ActualValue = "Missing parameters array"
			result.EvidenceCommand = "N/A"
		} else {
			allPass := true
			var failedParams []string
			var evidence []string
			
			for _, param := range ctrl.ParametersArray {
				checkResult := controls.CheckSysctlParameter(param.Name, param.ExpectedValue)
				evidence = append(evidence, fmt.Sprintf("%s=%s (%s)", param.Name, checkResult.ActualValue, checkResult.Status))
				if checkResult.Status != controls.StatusPass {
					allPass = false
					failedParams = append(failedParams, param.Name)
				}
			}
			
			if allPass {
				result.Status = "PASS"
				result.ActualValue = "All parameters configured correctly"
			} else {
				result.Status = "FAIL"
				result.ActualValue = fmt.Sprintf("Failed parameters: %s", strings.Join(failedParams, ", "))
			}
			result.EvidenceCommand = strings.Join(evidence, "; ")
		}

	case "SSHPrivateKeys":
		// Check SSH private host key files - default to /etc/ssh/ssh_host_*_key if not specified
		filePath := ctrl.FilePath
		if filePath == "" {
			filePath = "/etc/ssh/ssh_host_*_key"
		}
		expectedPerms := ctrl.ExpectedPermissions
		if expectedPerms == "" {
			expectedPerms = "600"
		}
		expectedOwner := ctrl.ExpectedOwner
		if expectedOwner == "" {
			expectedOwner = "root"
		}
		expectedGroup := ctrl.ExpectedGroup
		if expectedGroup == "" {
			expectedGroup = "root"
		}
		checkResult := controls.CheckFilePermissions(filePath, expectedPerms, expectedOwner, expectedGroup)
		result.Status = string(checkResult.Status)
		result.ActualValue = checkResult.ActualValue
		result.EvidenceCommand = checkResult.EvidenceCommand

	case "SSHPublicKeys":
		// Check SSH public host key files - default to /etc/ssh/ssh_host_*_key.pub if not specified
		filePath := ctrl.FilePath
		if filePath == "" {
			filePath = "/etc/ssh/ssh_host_*_key.pub"
		}
		expectedPerms := ctrl.ExpectedPermissions
		if expectedPerms == "" {
			expectedPerms = "644"
		}
		expectedOwner := ctrl.ExpectedOwner
		if expectedOwner == "" {
			expectedOwner = "root"
		}
		expectedGroup := ctrl.ExpectedGroup
		if expectedGroup == "" {
			expectedGroup = "root"
		}
		checkResult := controls.CheckFilePermissions(filePath, expectedPerms, expectedOwner, expectedGroup)
		result.Status = string(checkResult.Status)
		result.ActualValue = checkResult.ActualValue
		result.EvidenceCommand = checkResult.EvidenceCommand

	case "FilePermissions", "FilePermission", "LogFilePermissions":
		// LogFilePermissions might have log_directory instead of file_path
		filePath := ctrl.FilePath
		if filePath == "" && ctrl.LogDirectory != "" {
			filePath = ctrl.LogDirectory
		}
		// LogFilePermissions might have expected_file_permissions instead of expected_permissions
		expectedPerms := ctrl.ExpectedPermissions
		// Also check expected_mode (alternative field name)
		if expectedPerms == "" && ctrl.ExpectedMode != "" {
			expectedPerms = ctrl.ExpectedMode
		}
		if expectedPerms == "" && ctrl.ExpectedFilePerms != "" {
			expectedPerms = ctrl.ExpectedFilePerms
		}
		// If expected_permissions is missing, try to infer from control ID or title
		if expectedPerms == "" {
			// Common defaults based on file path
			if strings.Contains(filePath, "/etc/motd") || strings.Contains(filePath, "/etc/issue") {
				expectedPerms = "644"
			} else if strings.Contains(filePath, "/etc/cron") || strings.Contains(filePath, "/etc/at.allow") {
				expectedPerms = "600"
			} else {
				expectedPerms = "644" // Default
			}
		}
		if filePath == "" {
			result.Status = "ERROR"
			result.ActualValue = "Missing file_path or log_directory"
			result.EvidenceCommand = "N/A"
		} else {
			checkResult := controls.CheckFilePermissions(filePath, expectedPerms, ctrl.ExpectedOwner, ctrl.ExpectedGroup)
			result.Status = string(checkResult.Status)
			result.ActualValue = checkResult.ActualValue
			result.EvidenceCommand = checkResult.EvidenceCommand
		}

	case "FileContent", "ConfigFile":
		// ConfigFile might not have expected_result - try to infer from pattern or description
		expectedResult := ctrl.ExpectedResult
		if expectedResult == "" {
			// Infer from pattern or description
			pattern := strings.ToLower(ctrl.Pattern)
			desc := strings.ToLower(ctrl.Description)
			if strings.Contains(pattern, "nologin") || strings.Contains(desc, "not listed") || strings.Contains(desc, "not be") || strings.Contains(desc, "should not") {
				expectedResult = "not_found"
			} else if strings.Contains(desc, "not exist") || strings.Contains(desc, "missing") {
				expectedResult = "not_found"
			} else {
				expectedResult = "found"
			}
		}
		if ctrl.FilePath == "" || ctrl.Pattern == "" {
			result.Status = "ERROR"
			result.ActualValue = "Missing file_path or pattern"
			result.EvidenceCommand = "N/A"
		} else {
			checkResult := controls.CheckFileContent(ctrl.FilePath, ctrl.Pattern, expectedResult)
			result.Status = string(checkResult.Status)
			result.ActualValue = checkResult.ActualValue
			result.EvidenceCommand = checkResult.EvidenceCommand
		}

	case "SSHConfig", "SSHDConfig":
		checkResult := controls.CheckSSHConfig(ctrl.Parameter, ctrl.ExpectedValue, ctrl.Description)
		result.Status = string(checkResult.Status)
		result.ActualValue = checkResult.ActualValue
		result.EvidenceCommand = checkResult.EvidenceCommand

	case "PAMConfig":
		// PAMConfig might not have file_path - try to infer from control ID or description
		filePath := ctrl.FilePath
		if filePath == "" {
			// Try to infer PAM file from control ID or description
			if strings.Contains(ctrl.Description, "su command") || ctrl.ID == "5.2.7" {
				filePath = "/etc/pam.d/su"
			} else if strings.Contains(ctrl.Description, "pam_unix") || ctrl.ID == "5.3.2.1" {
				filePath = "/etc/pam.d/common-auth /etc/pam.d/common-account"
			} else if strings.Contains(ctrl.Description, "pam_faillock") || ctrl.ID == "5.3.2.2" {
				filePath = "/etc/pam.d/common-auth /etc/pam.d/common-account"
			} else if strings.Contains(ctrl.Description, "pam_pwquality") || ctrl.ID == "5.3.2.3" {
				filePath = "/etc/pam.d/common-password"
			} else if strings.Contains(ctrl.Description, "pam_pwhistory") || ctrl.ID == "5.3.2.4" {
				filePath = "/etc/pam.d/common-password"
			} else {
				// Default to common-auth
				filePath = "/etc/pam.d/common-auth"
			}
		}
		// Try to infer module_name and parameter from description if missing
		moduleName := ctrl.ModuleName
		param := ctrl.Parameter
		expectedValue := ctrl.ExpectedValue
		
		if moduleName == "" {
			if strings.Contains(ctrl.Description, "pam_unix") {
				moduleName = "pam_unix.so"
			} else if strings.Contains(ctrl.Description, "pam_faillock") {
				moduleName = "pam_faillock.so"
			} else if strings.Contains(ctrl.Description, "pam_pwquality") {
				moduleName = "pam_pwquality.so"
			} else if strings.Contains(ctrl.Description, "pam_pwhistory") {
				moduleName = "pam_pwhistory.so"
			} else if strings.Contains(ctrl.Description, "pam_wheel") {
				moduleName = "pam_wheel.so"
			}
		}
		
		// For PAM module enabled checks, expected_value should be "enabled" if not specified
		if expectedValue == "" && strings.Contains(ctrl.Description, "enabled") {
			expectedValue = "enabled"
		}
		
		// If still missing critical fields, mark as MANUAL
		if moduleName == "" && param == "" {
			result.Status = "MANUAL"
			result.ActualValue = "PAM configuration check requires manual verification"
			result.EvidenceCommand = "Check PAM configuration files manually"
		} else {
			checkResult := controls.CheckPAMConfig(filePath, moduleName, param, expectedValue, ctrl.Description)
			result.Status = string(checkResult.Status)
			result.ActualValue = checkResult.ActualValue
			result.EvidenceCommand = checkResult.EvidenceCommand
		}

	case "SudoConfig":
		checkResult := controls.CheckSudoConfig(ctrl.Parameter, ctrl.ExpectedValue, ctrl.Description)
		result.Status = string(checkResult.Status)
		result.ActualValue = checkResult.ActualValue
		result.EvidenceCommand = checkResult.EvidenceCommand

	case "CommandOutputEmpty":
		// Parse command - supports both simple commands and shell pipes
		auditCmd := strings.TrimSpace(ctrl.AuditCommand)
		if auditCmd == "" {
			result.Status = "ERROR"
			result.ActualValue = "Empty command"
			result.EvidenceCommand = ctrl.AuditCommand
		} else {
			// Split command into parts (preserving pipe characters in args)
			parts := strings.Fields(auditCmd)
			if len(parts) > 0 {
				cmdName := parts[0]
				args := parts[1:]
				// CheckCommandOutputEmpty will reconstruct full command and detect pipes
				// Pass control ID for nftables-specific logic
				checkResult := controls.CheckCommandOutputEmptyWithControl(cmdName, args, ctrl.Description, ctrl.ID)
				result.Status = string(checkResult.Status)
				result.ActualValue = checkResult.ActualValue
				result.EvidenceCommand = checkResult.Evidence.Source + ": " + checkResult.Evidence.Snippet
			} else {
				result.Status = "ERROR"
				result.ActualValue = "Invalid command format"
				result.EvidenceCommand = ctrl.AuditCommand
			}
		}

	case "FileExists":
		checkResult := controls.CheckFileExists(ctrl.FilePath, ctrl.Description)
		result.Status = string(checkResult.Status)
		result.ActualValue = checkResult.ActualValue
		result.EvidenceCommand = checkResult.EvidenceCommand

	case "DuplicateUIDs":
		// Check for duplicate UIDs in /etc/passwd
		auditCmd := ctrl.AuditCommand
		if auditCmd == "" {
			// Check control ID to determine the right command
			if ctrl.ID == "5.4.2.1" {
				// Ensure root is the only UID 0 account
				auditCmd = "awk -F: '($3 == 0) {print $1}' /etc/passwd | grep -v '^root$'"
			} else {
				// Default: check for duplicate UIDs
				auditCmd = "cut -d: -f3 /etc/passwd | sort | uniq -d"
			}
		}
		// CheckCommandOutputEmptyWithControl already handles pipes - just pass the command directly
		// It will detect pipes and use shell execution automatically
		parts := strings.Fields(auditCmd)
		if len(parts) > 0 {
			cmdName := parts[0]
			args := parts[1:]
			checkResult := controls.CheckCommandOutputEmptyWithControl(cmdName, args, ctrl.Description, ctrl.ID)
			result.Status = string(checkResult.Status)
			result.ActualValue = checkResult.ActualValue
			result.EvidenceCommand = checkResult.Evidence.Source + ": " + checkResult.Evidence.Snippet
		} else {
			result.Status = "ERROR"
			result.ActualValue = "Invalid command format"
			result.EvidenceCommand = auditCmd
		}

	case "DuplicateGIDs":
		// Check for duplicate GIDs in /etc/group
		auditCmd := ctrl.AuditCommand
		if auditCmd == "" {
			auditCmd = "cut -d: -f3 /etc/group | sort | uniq -d"
		}
		// CheckCommandOutputEmptyWithControl already handles pipes
		parts := strings.Fields(auditCmd)
		if len(parts) > 0 {
			cmdName := parts[0]
			args := parts[1:]
			checkResult := controls.CheckCommandOutputEmptyWithControl(cmdName, args, ctrl.Description, ctrl.ID)
			result.Status = string(checkResult.Status)
			result.ActualValue = checkResult.ActualValue
			result.EvidenceCommand = checkResult.Evidence.Source + ": " + checkResult.Evidence.Snippet
		} else {
			result.Status = "ERROR"
			result.ActualValue = "Invalid command format"
			result.EvidenceCommand = auditCmd
		}

	case "DuplicateUsernames":
		// Check for duplicate usernames in /etc/passwd
		auditCmd := ctrl.AuditCommand
		if auditCmd == "" {
			auditCmd = "cut -d: -f1 /etc/passwd | sort | uniq -d"
		}
		// CheckCommandOutputEmptyWithControl already handles pipes
		parts := strings.Fields(auditCmd)
		if len(parts) > 0 {
			cmdName := parts[0]
			args := parts[1:]
			checkResult := controls.CheckCommandOutputEmptyWithControl(cmdName, args, ctrl.Description, ctrl.ID)
			result.Status = string(checkResult.Status)
			result.ActualValue = checkResult.ActualValue
			result.EvidenceCommand = checkResult.Evidence.Source + ": " + checkResult.Evidence.Snippet
		} else {
			result.Status = "ERROR"
			result.ActualValue = "Invalid command format"
			result.EvidenceCommand = auditCmd
		}

	case "DuplicateGroupnames":
		// Check for duplicate group names in /etc/group
		auditCmd := ctrl.AuditCommand
		if auditCmd == "" {
			auditCmd = "cut -d: -f1 /etc/group | sort | uniq -d"
		}
		// CheckCommandOutputEmptyWithControl already handles pipes
		parts := strings.Fields(auditCmd)
		if len(parts) > 0 {
			cmdName := parts[0]
			args := parts[1:]
			checkResult := controls.CheckCommandOutputEmptyWithControl(cmdName, args, ctrl.Description, ctrl.ID)
			result.Status = string(checkResult.Status)
			result.ActualValue = checkResult.ActualValue
			result.EvidenceCommand = checkResult.Evidence.Source + ": " + checkResult.Evidence.Snippet
		} else {
			result.Status = "ERROR"
			result.ActualValue = "Invalid command format"
			result.EvidenceCommand = auditCmd
		}

	case "WorldWritableFiles":
		// Check for world writable files
		auditCmd := ctrl.AuditCommand
		if auditCmd == "" {
			// Default audit command: find world writable files (excluding proc, sys, dev)
			auditCmd = "find / -xdev -type f -perm -0002 ! -path '/proc/*' ! -path '/sys/*' ! -path '/dev/*' 2>/dev/null"
		}
		parts := strings.Fields(auditCmd)
		if len(parts) > 0 {
			cmdName := parts[0]
			args := parts[1:]
			checkResult := controls.CheckCommandOutputEmptyWithControl(cmdName, args, ctrl.Description, ctrl.ID)
			result.Status = string(checkResult.Status)
			result.ActualValue = checkResult.ActualValue
			result.EvidenceCommand = checkResult.Evidence.Source + ": " + checkResult.Evidence.Snippet
		} else {
			result.Status = "ERROR"
			result.ActualValue = "Invalid command format"
			result.EvidenceCommand = auditCmd
		}

	case "OrphanedFiles":
		// Check for files without owner/group
		auditCmd := ctrl.AuditCommand
		if auditCmd == "" {
			// Default audit command: find files without owner or group
			auditCmd = "find / -xdev \\( -nouser -o -nogroup \\) 2>/dev/null"
		}
		parts := strings.Fields(auditCmd)
		if len(parts) > 0 {
			cmdName := parts[0]
			args := parts[1:]
			checkResult := controls.CheckCommandOutputEmptyWithControl(cmdName, args, ctrl.Description, ctrl.ID)
			result.Status = string(checkResult.Status)
			result.ActualValue = checkResult.ActualValue
			result.EvidenceCommand = checkResult.Evidence.Source + ": " + checkResult.Evidence.Snippet
		} else {
			result.Status = "ERROR"
			result.ActualValue = "Invalid command format"
			result.EvidenceCommand = auditCmd
		}

	case "UFWStatus":
		// Check UFW service status
		auditCmd := ctrl.AuditCommand
		if auditCmd == "" {
			// Default: check if ufw service is active
			// Handle both expected_status and expected_state (normalized in Normalize())
			expectedStatus := ctrl.ExpectedStatus
			if expectedStatus == "" && ctrl.ExpectedState != "" {
				expectedStatus = ctrl.ExpectedState
			}
			if expectedStatus == "" {
				expectedStatus = "active"
			}
			// Use service check instead of command
			checkResult := controls.CheckServiceStatus("ufw", expectedStatus)
			result.Status = string(checkResult.Status)
			result.ActualValue = checkResult.ActualValue
			result.EvidenceCommand = checkResult.EvidenceCommand
		} else {
			parts := strings.Fields(auditCmd)
			if len(parts) > 0 {
				cmdName := parts[0]
				args := parts[1:]
				checkResult := controls.CheckCommandOutputEmptyWithControl(cmdName, args, ctrl.Description, ctrl.ID)
				result.Status = string(checkResult.Status)
				result.ActualValue = checkResult.ActualValue
				result.EvidenceCommand = checkResult.Evidence.Source + ": " + checkResult.Evidence.Snippet
			} else {
				result.Status = "ERROR"
				result.ActualValue = "Invalid command format"
				result.EvidenceCommand = auditCmd
			}
		}

	case "UFWLoopback", "UFWOpenPorts", "UFWDefaultPolicy", "UFWWithNftables":
		// UFW checks use CommandOutputEmpty
		auditCmd := ctrl.AuditCommand
		if auditCmd == "" {
			result.Status = "ERROR"
			result.ActualValue = "Missing audit command"
			result.EvidenceCommand = "N/A"
		} else {
			parts := strings.Fields(auditCmd)
			if len(parts) > 0 {
				cmdName := parts[0]
				args := parts[1:]
				checkResult := controls.CheckCommandOutputEmptyWithControl(cmdName, args, ctrl.Description, ctrl.ID)
				result.Status = string(checkResult.Status)
				result.ActualValue = checkResult.ActualValue
				result.EvidenceCommand = checkResult.Evidence.Source + ": " + checkResult.Evidence.Snippet
			} else {
				result.Status = "ERROR"
				result.ActualValue = "Invalid command format"
				result.EvidenceCommand = auditCmd
			}
		}

	case "NftablesTable":
		// Check if nftables table exists
		auditCmd := ctrl.AuditCommand
		if auditCmd == "" {
			// Default: check if nftables has any tables
			auditCmd = "nft list tables"
		}
		parts := strings.Fields(auditCmd)
		if len(parts) > 0 {
			cmdName := parts[0]
			args := parts[1:]
			checkResult := controls.CheckCommandOutputEmptyWithControl(cmdName, args, ctrl.Description, ctrl.ID)
			result.Status = string(checkResult.Status)
			result.ActualValue = checkResult.ActualValue
			result.EvidenceCommand = checkResult.Evidence.Source + ": " + checkResult.Evidence.Snippet
		} else {
			result.Status = "ERROR"
			result.ActualValue = "Invalid command format"
			result.EvidenceCommand = auditCmd
		}

	case "NftablesBaseChains":
		// Check if nftables base chains exist
		auditCmd := ctrl.AuditCommand
		if auditCmd == "" {
			auditCmd = "nft list chains | grep -E '(input|forward|output)'"
		}
		parts := strings.Fields(auditCmd)
		if len(parts) > 0 {
			cmdName := parts[0]
			args := parts[1:]
			checkResult := controls.CheckCommandOutputEmptyWithControl(cmdName, args, ctrl.Description, ctrl.ID)
			result.Status = string(checkResult.Status)
			result.ActualValue = checkResult.ActualValue
			result.EvidenceCommand = checkResult.Evidence.Source + ": " + checkResult.Evidence.Snippet
		} else {
			result.Status = "ERROR"
			result.ActualValue = "Invalid command format"
			result.EvidenceCommand = auditCmd
		}

	case "NftablesLoopback":
		// Check nftables loopback traffic
		auditCmd := ctrl.AuditCommand
		if auditCmd == "" {
			auditCmd = "nft list ruleset | grep -E '(iif.*lo|127.0.0.0/8)'"
		}
		parts := strings.Fields(auditCmd)
		if len(parts) > 0 {
			cmdName := parts[0]
			args := parts[1:]
			checkResult := controls.CheckCommandOutputEmptyWithControl(cmdName, args, ctrl.Description, ctrl.ID)
			result.Status = string(checkResult.Status)
			result.ActualValue = checkResult.ActualValue
			result.EvidenceCommand = checkResult.Evidence.Source + ": " + checkResult.Evidence.Snippet
		} else {
			result.Status = "ERROR"
			result.ActualValue = "Invalid command format"
			result.EvidenceCommand = auditCmd
		}

	case "NftablesDefaultPolicy":
		// Check nftables default policy
		auditCmd := ctrl.AuditCommand
		if auditCmd == "" {
			auditCmd = "nft list chains | grep -E 'policy drop'"
		}
		parts := strings.Fields(auditCmd)
		if len(parts) > 0 {
			cmdName := parts[0]
			args := parts[1:]
			checkResult := controls.CheckCommandOutputEmptyWithControl(cmdName, args, ctrl.Description, ctrl.ID)
			result.Status = string(checkResult.Status)
			result.ActualValue = checkResult.ActualValue
			result.EvidenceCommand = checkResult.Evidence.Source + ": " + checkResult.Evidence.Snippet
		} else {
			result.Status = "ERROR"
			result.ActualValue = "Invalid command format"
			result.EvidenceCommand = auditCmd
		}

	case "NftablesPersistent":
		// Check if nftables rules are persistent
		auditCmd := ctrl.AuditCommand
		if auditCmd == "" {
			auditCmd = "grep -E 'include.*nftables' /etc/nftables.conf"
		}
		parts := strings.Fields(auditCmd)
		if len(parts) > 0 {
			cmdName := parts[0]
			args := parts[1:]
			checkResult := controls.CheckCommandOutputEmptyWithControl(cmdName, args, ctrl.Description, ctrl.ID)
			result.Status = string(checkResult.Status)
			result.ActualValue = checkResult.ActualValue
			result.EvidenceCommand = checkResult.Evidence.Source + ": " + checkResult.Evidence.Snippet
		} else {
			result.Status = "ERROR"
			result.ActualValue = "Invalid command format"
			result.EvidenceCommand = auditCmd
		}

	case "ShadowedPasswords":
		// Check if /etc/passwd uses shadowed passwords (x in second field)
		filePath := ctrl.FilePath
		if filePath == "" && ctrl.PasswdFile != "" {
			filePath = ctrl.PasswdFile
		}
		if filePath == "" {
			filePath = "/etc/passwd"
		}
		// Check that all entries have 'x' in the password field (shadowed)
		checkResult := controls.CheckFileContent(filePath, "^[^:]+:x:", "found")
		result.Status = string(checkResult.Status)
		result.ActualValue = checkResult.ActualValue
		result.EvidenceCommand = checkResult.EvidenceCommand

	case "EmptyPasswords":
		// Check for empty password fields in /etc/shadow
		filePath := ctrl.FilePath
		if filePath == "" && ctrl.ShadowFile != "" {
			filePath = ctrl.ShadowFile
		}
		if filePath == "" {
			filePath = "/etc/shadow"
		}
		// Check that no entries have empty password field (second field should not be empty)
		checkResult := controls.CheckFileContent(filePath, "^[^:]+::", "not_found")
		result.Status = string(checkResult.Status)
		result.ActualValue = checkResult.ActualValue
		result.EvidenceCommand = checkResult.EvidenceCommand

	case "EmptyGroup":
		// Check that shadow group is empty
		auditCmd := ctrl.AuditCommand
		if auditCmd == "" {
			auditCmd = "awk -F: '($1==\"shadow\") {print $NF}' /etc/group"
		}
		// CheckCommandOutputEmptyWithControl handles shell constructs
		parts := strings.Fields(auditCmd)
		if len(parts) > 0 {
			cmdName := parts[0]
			args := parts[1:]
			checkResult := controls.CheckCommandOutputEmptyWithControl(cmdName, args, ctrl.Description, ctrl.ID)
			result.Status = string(checkResult.Status)
			result.ActualValue = checkResult.ActualValue
			result.EvidenceCommand = checkResult.Evidence.Source + ": " + checkResult.Evidence.Snippet
		} else {
			result.Status = "ERROR"
			result.ActualValue = "Invalid command format"
			result.EvidenceCommand = auditCmd
		}

	case "GroupConsistency":
		// Check that all groups in /etc/passwd exist in /etc/group
		auditCmd := ctrl.AuditCommand
		if auditCmd == "" {
			auditCmd = "for i in $(cut -s -d: -f4 /etc/passwd | sort -u); do grep -q -P \"^.*?:[^:]*:$i:\" /etc/group || echo \"Group $i is referenced by /etc/passwd but does not exist in /etc/group\"; done"
		}
		// CheckCommandOutputEmptyWithControl handles shell constructs - pass as single command
		// For shell scripts, we need to pass via sh -c
		checkResult := controls.CheckCommandOutputEmptyWithControl("sh", []string{"-c", auditCmd}, ctrl.Description, ctrl.ID)
		result.Status = string(checkResult.Status)
		result.ActualValue = checkResult.ActualValue
		result.EvidenceCommand = checkResult.Evidence.Source + ": " + checkResult.Evidence.Snippet

	case "UserHomeDirs":
		// Check that user home directories exist and have correct permissions
		auditCmd := ctrl.AuditCommand
		if auditCmd == "" {
			auditCmd = "awk -F: '($1!~/(halt|sync|shutdown|nfsnobody)/ && $7!~/^\\/sbin\\/nologin$/ && $7!~/^\\/bin\\/false$/ && $3<1000) {print $1\":\"$6}' /etc/passwd | while IFS=: read -r user dir; do if [ ! -d \"$dir\" ]; then echo \"User $user home directory $dir does not exist\"; fi; done"
		}
		// Shell scripts with pipes and conditionals - pass via sh -c
		checkResult := controls.CheckCommandOutputEmptyWithControl("sh", []string{"-c", auditCmd}, ctrl.Description, ctrl.ID)
		result.Status = string(checkResult.Status)
		result.ActualValue = checkResult.ActualValue
		result.EvidenceCommand = checkResult.Evidence.Source + ": " + checkResult.Evidence.Snippet

	case "UserDotFiles":
		// Check that user dot files have correct permissions
		auditCmd := ctrl.AuditCommand
		if auditCmd == "" {
			auditCmd = "awk -F: '($1!~/(halt|sync|shutdown|nfsnobody)/ && $7!~/^\\/sbin\\/nologin$/ && $7!~/^\\/bin\\/false$/ && $3<1000) {print $6}' /etc/passwd | while read -r dir; do if [ -d \"$dir\" ]; then for file in \"$dir\"/.[^.]*; do if [ ! -h \"$file\" ] && [ -f \"$file\" ]; then perms=$(stat -L -c \"%a\" \"$file\"); if [ \"$perms\" -gt 750 ]; then echo \"$file has permissions $perms\"; fi; fi; done; fi; done"
		}
		// Shell scripts with pipes, loops, and conditionals - pass via sh -c
		checkResult := controls.CheckCommandOutputEmptyWithControl("sh", []string{"-c", auditCmd}, ctrl.Description, ctrl.ID)
		result.Status = string(checkResult.Status)
		result.ActualValue = checkResult.ActualValue
		result.EvidenceCommand = checkResult.Evidence.Source + ": " + checkResult.Evidence.Snippet

	case "BootParameter":
		// Check boot parameters - BootParameter uses BootParametersArray (array of strings like "apparmor=1")
		// The parameters field is unmarshaled into BootParametersArray by UnmarshalJSON
		bootParams := ctrl.BootParametersArray
		if len(bootParams) == 0 {
			// If BootParametersArray is empty, try to read from the raw Parameters field
			// This shouldn't happen if UnmarshalJSON worked, but handle it as fallback
			var params []string
			if err := json.Unmarshal(ctrl.Parameters, &params); err == nil && len(params) > 0 {
				bootParams = params
			}
		}
		
		if len(bootParams) > 0 {
			allPass := true
			var failedParams []string
			var evidence []string
			
			// Check /proc/cmdline first (runtime)
			cmdlineContent := ""
			if cmdlineBytes, err := os.ReadFile("/proc/cmdline"); err == nil {
				cmdlineContent = string(cmdlineBytes)
			}
			
			// Also check /etc/default/grub (persistent config)
			grubContent := ""
			if grubBytes, err := os.ReadFile("/etc/default/grub"); err == nil {
				grubContent = string(grubBytes)
			}
			
			for _, param := range bootParams {
				// Extract parameter name (before =)
				paramName := param
				if idx := strings.Index(param, "="); idx > 0 {
					paramName = param[:idx]
				}
				
				// Check if parameter exists in /proc/cmdline or /etc/default/grub
				foundInCmdline := strings.Contains(cmdlineContent, paramName)
				foundInGrub := strings.Contains(grubContent, paramName)
				
				if foundInCmdline || foundInGrub {
					evidence = append(evidence, fmt.Sprintf("%s: found", paramName))
				} else {
					allPass = false
					failedParams = append(failedParams, paramName)
					evidence = append(evidence, fmt.Sprintf("%s: not found", paramName))
				}
			}
			
			if allPass {
				result.Status = "PASS"
				result.ActualValue = "All boot parameters configured"
			} else {
				result.Status = "FAIL"
				result.ActualValue = fmt.Sprintf("Missing parameters: %s", strings.Join(failedParams, ", "))
			}
			result.EvidenceCommand = strings.Join(evidence, "; ")
		} else if ctrl.FilePath != "" && ctrl.Pattern != "" {
			// FileContent check
			checkResult := controls.CheckFileContent(ctrl.FilePath, ctrl.Pattern, ctrl.ExpectedResult)
			result.Status = string(checkResult.Status)
			result.ActualValue = checkResult.ActualValue
			result.EvidenceCommand = checkResult.EvidenceCommand
		} else {
			// Default: check /proc/cmdline for common boot parameters
			result.Status = "MANUAL"
			result.ActualValue = "Boot parameter check requires manual verification"
			result.EvidenceCommand = "Check /proc/cmdline and /etc/default/grub"
		}

	case "AppArmorProfile":
		// Check AppArmor profiles - use aa-status command
		if ctrl.FilePath != "" && ctrl.Pattern != "" {
			expectedResult := ctrl.ExpectedResult
			if expectedResult == "" {
				expectedResult = "found"
			}
			checkResult := controls.CheckFileContent(ctrl.FilePath, ctrl.Pattern, expectedResult)
			result.Status = string(checkResult.Status)
			result.ActualValue = checkResult.ActualValue
			result.EvidenceCommand = checkResult.EvidenceCommand
		} else if ctrl.AuditCommand != "" {
			parts := strings.Fields(ctrl.AuditCommand)
			if len(parts) > 0 {
				cmdName := parts[0]
				args := parts[1:]
				checkResult := controls.CheckCommandOutputEmptyWithControl(cmdName, args, ctrl.Description, ctrl.ID)
				result.Status = string(checkResult.Status)
				result.ActualValue = checkResult.ActualValue
				result.EvidenceCommand = checkResult.Evidence.Source + ": " + checkResult.Evidence.Snippet
			} else {
				result.Status = "ERROR"
				result.ActualValue = "Invalid control configuration"
				result.EvidenceCommand = "N/A"
			}
		} else {
			// Default: check if AppArmor is enabled and profiles exist
			auditCmd := "aa-status --enabled 2>/dev/null && aa-status 2>/dev/null | grep -E '(enforce|complain)'"
			checkResult := controls.CheckCommandOutputEmptyWithControl("sh", []string{"-c", auditCmd}, ctrl.Description, ctrl.ID)
			result.Status = string(checkResult.Status)
			result.ActualValue = checkResult.ActualValue
			result.EvidenceCommand = checkResult.Evidence.Source + ": " + checkResult.Evidence.Snippet
		}

	case "CoreDumpRestriction":
		// Check core dump restrictions - check /etc/security/limits.conf and sysctl
		if ctrl.FilePath != "" && ctrl.Pattern != "" {
			expectedResult := ctrl.ExpectedResult
			if expectedResult == "" {
				expectedResult = "found"
			}
			checkResult := controls.CheckFileContent(ctrl.FilePath, ctrl.Pattern, expectedResult)
			result.Status = string(checkResult.Status)
			result.ActualValue = checkResult.ActualValue
			result.EvidenceCommand = checkResult.EvidenceCommand
		} else if ctrl.AuditCommand != "" {
			parts := strings.Fields(ctrl.AuditCommand)
			if len(parts) > 0 {
				cmdName := parts[0]
				args := parts[1:]
				checkResult := controls.CheckCommandOutputEmptyWithControl(cmdName, args, ctrl.Description, ctrl.ID)
				result.Status = string(checkResult.Status)
				result.ActualValue = checkResult.ActualValue
				result.EvidenceCommand = checkResult.Evidence.Source + ": " + checkResult.Evidence.Snippet
			} else {
				result.Status = "ERROR"
				result.ActualValue = "Invalid control configuration"
				result.EvidenceCommand = "N/A"
			}
		} else {
			// Default: check sysctl fs.suid_dumpable and /etc/security/limits.conf
			sysctlResult := controls.CheckSysctlParameter("fs.suid_dumpable", "0")
			if sysctlResult.Status == controls.StatusPass {
				result.Status = "PASS"
				result.ActualValue = sysctlResult.ActualValue
			} else {
				// Also check limits.conf
				limitsResult := controls.CheckFileContent("/etc/security/limits.conf", "\\*.*hard.*core.*0", "found")
				if limitsResult.Status == controls.StatusPass {
					result.Status = "PASS"
					result.ActualValue = "Core dump restricted in limits.conf"
				} else {
					result.Status = "FAIL"
					result.ActualValue = "Core dump restrictions not configured"
				}
			}
			result.EvidenceCommand = "Check sysctl fs.suid_dumpable and /etc/security/limits.conf"
		}

	case "MTALocalOnly":
		// Check MTA local-only mode - check postfix main.cf
		if ctrl.FilePath != "" && ctrl.Pattern != "" {
			expectedResult := ctrl.ExpectedResult
			if expectedResult == "" {
				expectedResult = "found"
			}
			checkResult := controls.CheckFileContent(ctrl.FilePath, ctrl.Pattern, expectedResult)
			result.Status = string(checkResult.Status)
			result.ActualValue = checkResult.ActualValue
			result.EvidenceCommand = checkResult.EvidenceCommand
		} else {
			// Default: check /etc/postfix/main.cf for inet_interfaces
			checkResult := controls.CheckFileContent("/etc/postfix/main.cf", "inet_interfaces.*localhost", "found")
			result.Status = string(checkResult.Status)
			result.ActualValue = checkResult.ActualValue
			result.EvidenceCommand = checkResult.EvidenceCommand
		}

	case "WirelessInterface":
		// Check for wireless interfaces
		if ctrl.FilePath != "" && ctrl.Pattern != "" {
			expectedResult := ctrl.ExpectedResult
			if expectedResult == "" {
				expectedResult = "not_found"
			}
			checkResult := controls.CheckFileContent(ctrl.FilePath, ctrl.Pattern, expectedResult)
			result.Status = string(checkResult.Status)
			result.ActualValue = checkResult.ActualValue
			result.EvidenceCommand = checkResult.EvidenceCommand
		} else if ctrl.AuditCommand != "" {
			parts := strings.Fields(ctrl.AuditCommand)
			if len(parts) > 0 {
				cmdName := parts[0]
				args := parts[1:]
				checkResult := controls.CheckCommandOutputEmptyWithControl(cmdName, args, ctrl.Description, ctrl.ID)
				result.Status = string(checkResult.Status)
				result.ActualValue = checkResult.ActualValue
				result.EvidenceCommand = checkResult.Evidence.Source + ": " + checkResult.Evidence.Snippet
			} else {
				result.Status = "ERROR"
				result.ActualValue = "Invalid control configuration"
				result.EvidenceCommand = "N/A"
			}
		} else {
			// Default: check for wireless interfaces using ip/iw
			auditCmd := "ip link show | grep -i wireless || iw dev 2>/dev/null | grep -i interface"
			checkResult := controls.CheckCommandOutputEmptyWithControl("sh", []string{"-c", auditCmd}, ctrl.Description, ctrl.ID)
			result.Status = string(checkResult.Status)
			result.ActualValue = checkResult.ActualValue
			result.EvidenceCommand = checkResult.Evidence.Source + ": " + checkResult.Evidence.Snippet
		}

	case "SingleLoggingSystem":
		// Check that only one logging system is in use
		if ctrl.FilePath != "" && ctrl.Pattern != "" {
			expectedResult := ctrl.ExpectedResult
			if expectedResult == "" {
				expectedResult = "found"
			}
			checkResult := controls.CheckFileContent(ctrl.FilePath, ctrl.Pattern, expectedResult)
			result.Status = string(checkResult.Status)
			result.ActualValue = checkResult.ActualValue
			result.EvidenceCommand = checkResult.EvidenceCommand
		} else if ctrl.AuditCommand != "" {
			parts := strings.Fields(ctrl.AuditCommand)
			if len(parts) > 0 {
				cmdName := parts[0]
				args := parts[1:]
				checkResult := controls.CheckCommandOutputEmptyWithControl(cmdName, args, ctrl.Description, ctrl.ID)
				result.Status = string(checkResult.Status)
				result.ActualValue = checkResult.ActualValue
				result.EvidenceCommand = checkResult.Evidence.Source + ": " + checkResult.Evidence.Snippet
			} else {
				result.Status = "ERROR"
				result.ActualValue = "Invalid control configuration"
				result.EvidenceCommand = "N/A"
			}
		} else {
			// Default: check if both rsyslog and journald are active (should fail)
			rsyslogActive := controls.CheckServiceStatus("rsyslog", "active")
			journaldActive := controls.CheckServiceStatus("systemd-journald", "active")
			if rsyslogActive.Status == controls.StatusPass && journaldActive.Status == controls.StatusPass {
				result.Status = "FAIL"
				result.ActualValue = "Both rsyslog and journald are active"
			} else {
				result.Status = "PASS"
				result.ActualValue = "Only one logging system active"
			}
			result.EvidenceCommand = fmt.Sprintf("rsyslog: %s, journald: %s", rsyslogActive.ActualValue, journaldActive.ActualValue)
		}

	case "SingleFirewall":
		// Check that only one firewall is in use
		if ctrl.FilePath != "" && ctrl.Pattern != "" {
			expectedResult := ctrl.ExpectedResult
			if expectedResult == "" {
				expectedResult = "found"
			}
			checkResult := controls.CheckFileContent(ctrl.FilePath, ctrl.Pattern, expectedResult)
			result.Status = string(checkResult.Status)
			result.ActualValue = checkResult.ActualValue
			result.EvidenceCommand = checkResult.EvidenceCommand
		} else if ctrl.AuditCommand != "" {
			parts := strings.Fields(ctrl.AuditCommand)
			if len(parts) > 0 {
				cmdName := parts[0]
				args := parts[1:]
				checkResult := controls.CheckCommandOutputEmptyWithControl(cmdName, args, ctrl.Description, ctrl.ID)
				result.Status = string(checkResult.Status)
				result.ActualValue = checkResult.ActualValue
				result.EvidenceCommand = checkResult.Evidence.Source + ": " + checkResult.Evidence.Snippet
			} else {
				result.Status = "ERROR"
				result.ActualValue = "Invalid control configuration"
				result.EvidenceCommand = "N/A"
			}
		} else {
			// Default: check if multiple firewalls are active (ufw, nftables, iptables)
			ufwActive := controls.CheckServiceStatus("ufw", "active")
			nftActive := controls.CheckServiceStatus("nftables", "active")
			activeCount := 0
			if ufwActive.Status == controls.StatusPass {
				activeCount++
			}
			if nftActive.Status == controls.StatusPass {
				activeCount++
			}
			if activeCount > 1 {
				result.Status = "FAIL"
				result.ActualValue = fmt.Sprintf("Multiple firewalls active (%d)", activeCount)
			} else {
				result.Status = "PASS"
				result.ActualValue = "Only one firewall active"
			}
			result.EvidenceCommand = fmt.Sprintf("ufw: %s, nftables: %s", ufwActive.ActualValue, nftActive.ActualValue)
		}

	case "JournaldConfig":
		// Check journald configuration
		if ctrl.FilePath != "" && ctrl.Pattern != "" {
			expectedResult := ctrl.ExpectedResult
			if expectedResult == "" {
				expectedResult = "found"
			}
			checkResult := controls.CheckFileContent(ctrl.FilePath, ctrl.Pattern, expectedResult)
			result.Status = string(checkResult.Status)
			result.ActualValue = checkResult.ActualValue
			result.EvidenceCommand = checkResult.EvidenceCommand
		} else if ctrl.AuditCommand != "" {
			parts := strings.Fields(ctrl.AuditCommand)
			if len(parts) > 0 {
				cmdName := parts[0]
				args := parts[1:]
				checkResult := controls.CheckCommandOutputEmptyWithControl(cmdName, args, ctrl.Description, ctrl.ID)
				result.Status = string(checkResult.Status)
				result.ActualValue = checkResult.ActualValue
				result.EvidenceCommand = checkResult.Evidence.Source + ": " + checkResult.Evidence.Snippet
			} else {
				result.Status = "ERROR"
				result.ActualValue = "Invalid control configuration"
				result.EvidenceCommand = "N/A"
			}
		} else {
			// Default: check /etc/systemd/journald.conf
			// Try to infer from control ID
			var filePath, pattern string
			if ctrl.ID == "6.1.2.2" {
				filePath = "/etc/systemd/journald.conf"
				pattern = "ForwardToSyslog=no"
			} else if ctrl.ID == "6.1.2.3" {
				filePath = "/etc/systemd/journald.conf"
				pattern = "Compress=yes"
			} else if ctrl.ID == "6.1.2.4" {
				filePath = "/etc/systemd/journald.conf"
				pattern = "Storage=persistent"
			} else {
				filePath = "/etc/systemd/journald.conf"
				pattern = "."
			}
			checkResult := controls.CheckFileContent(filePath, pattern, "found")
			result.Status = string(checkResult.Status)
			result.ActualValue = checkResult.ActualValue
			result.EvidenceCommand = checkResult.EvidenceCommand
		}

	case "RsyslogConfig":
		// Check rsyslog configuration
		if ctrl.FilePath != "" && ctrl.Pattern != "" {
			expectedResult := ctrl.ExpectedResult
			if expectedResult == "" {
				expectedResult = "found"
			}
			checkResult := controls.CheckFileContent(ctrl.FilePath, ctrl.Pattern, expectedResult)
			result.Status = string(checkResult.Status)
			result.ActualValue = checkResult.ActualValue
			result.EvidenceCommand = checkResult.EvidenceCommand
		} else if ctrl.AuditCommand != "" {
			parts := strings.Fields(ctrl.AuditCommand)
			if len(parts) > 0 {
				cmdName := parts[0]
				args := parts[1:]
				checkResult := controls.CheckCommandOutputEmptyWithControl(cmdName, args, ctrl.Description, ctrl.ID)
				result.Status = string(checkResult.Status)
				result.ActualValue = checkResult.ActualValue
				result.EvidenceCommand = checkResult.Evidence.Source + ": " + checkResult.Evidence.Snippet
			} else {
				result.Status = "ERROR"
				result.ActualValue = "Invalid control configuration"
				result.EvidenceCommand = "N/A"
			}
		} else {
			// Default: check /etc/rsyslog.conf
			checkResult := controls.CheckFileContent("/etc/rsyslog.conf", ".", "found")
			result.Status = string(checkResult.Status)
			result.ActualValue = checkResult.ActualValue
			result.EvidenceCommand = checkResult.EvidenceCommand
		}

	case "CronJob":
		// Check cron job configuration
		if ctrl.FilePath != "" && ctrl.Pattern != "" {
			expectedResult := ctrl.ExpectedResult
			if expectedResult == "" {
				expectedResult = "found"
			}
			checkResult := controls.CheckFileContent(ctrl.FilePath, ctrl.Pattern, expectedResult)
			result.Status = string(checkResult.Status)
			result.ActualValue = checkResult.ActualValue
			result.EvidenceCommand = checkResult.EvidenceCommand
		} else if ctrl.AuditCommand != "" {
			parts := strings.Fields(ctrl.AuditCommand)
			if len(parts) > 0 {
				cmdName := parts[0]
				args := parts[1:]
				checkResult := controls.CheckCommandOutputEmptyWithControl(cmdName, args, ctrl.Description, ctrl.ID)
				result.Status = string(checkResult.Status)
				result.ActualValue = checkResult.ActualValue
				result.EvidenceCommand = checkResult.Evidence.Source + ": " + checkResult.Evidence.Snippet
			} else {
				result.Status = "ERROR"
				result.ActualValue = "Invalid control configuration"
				result.EvidenceCommand = "N/A"
			}
		} else {
			// Default: check if cron service is enabled and AIDE cron job exists
			cronEnabled := controls.CheckServiceStatus("cron", "enabled")
			if cronEnabled.Status == controls.StatusPass {
				// Check for AIDE cron job
				aideCron := controls.CheckFileContent("/etc/cron.daily/aide", ".", "found")
				if aideCron.Status == controls.StatusPass {
					result.Status = "PASS"
					result.ActualValue = "Cron enabled and AIDE job configured"
				} else {
					result.Status = "FAIL"
					result.ActualValue = "Cron enabled but AIDE job not found"
				}
			} else {
				result.Status = "FAIL"
				result.ActualValue = "Cron service not enabled"
			}
			result.EvidenceCommand = fmt.Sprintf("cron: %s", cronEnabled.ActualValue)
		}

	case "AIDEConfig":
		// Check AIDE configuration
		if ctrl.FilePath != "" && ctrl.Pattern != "" {
			expectedResult := ctrl.ExpectedResult
			if expectedResult == "" {
				expectedResult = "found"
			}
			checkResult := controls.CheckFileContent(ctrl.FilePath, ctrl.Pattern, expectedResult)
			result.Status = string(checkResult.Status)
			result.ActualValue = checkResult.ActualValue
			result.EvidenceCommand = checkResult.EvidenceCommand
		} else if ctrl.AuditCommand != "" {
			parts := strings.Fields(ctrl.AuditCommand)
			if len(parts) > 0 {
				cmdName := parts[0]
				args := parts[1:]
				checkResult := controls.CheckCommandOutputEmptyWithControl(cmdName, args, ctrl.Description, ctrl.ID)
				result.Status = string(checkResult.Status)
				result.ActualValue = checkResult.ActualValue
				result.EvidenceCommand = checkResult.Evidence.Source + ": " + checkResult.Evidence.Snippet
			} else {
				result.Status = "ERROR"
				result.ActualValue = "Invalid control configuration"
				result.EvidenceCommand = "N/A"
			}
		} else {
			// Default: check if AIDE config exists
			checkResult := controls.CheckFileExists("/etc/aide/aide.conf", ctrl.Description)
			result.Status = string(checkResult.Status)
			result.ActualValue = checkResult.ActualValue
			result.EvidenceCommand = checkResult.EvidenceCommand
		}

	case "Manual":
		// Explicitly manual - should have been caught earlier, but handle it here too
		result.Status = "MANUAL"
		result.ActualValue = "Manual verification required"
		result.EvidenceCommand = "N/A"
		result.Description = "This control requires manual verification"

	default:
		// For unknown types, try to infer from available fields
		// Try multiple strategies before giving up
		
		// Strategy 1: FileContent (file_path + pattern)
		if ctrl.FilePath != "" && ctrl.Pattern != "" {
			checkResult := controls.CheckFileContent(ctrl.FilePath, ctrl.Pattern, ctrl.ExpectedResult)
			result.Status = string(checkResult.Status)
			result.ActualValue = checkResult.ActualValue
			result.EvidenceCommand = checkResult.EvidenceCommand
		// Strategy 2: FilePermissions (file_path + expected_permissions or expected_mode)
		} else if ctrl.FilePath != "" && (ctrl.ExpectedPermissions != "" || ctrl.ExpectedMode != "") {
			expectedPerms := ctrl.ExpectedPermissions
			if expectedPerms == "" && ctrl.ExpectedMode != "" {
				expectedPerms = ctrl.ExpectedMode
			}
			checkResult := controls.CheckFilePermissions(ctrl.FilePath, expectedPerms, ctrl.ExpectedOwner, ctrl.ExpectedGroup)
			result.Status = string(checkResult.Status)
			result.ActualValue = checkResult.ActualValue
			result.EvidenceCommand = checkResult.EvidenceCommand
		// Strategy 3: CommandOutputEmpty (audit_command)
		} else if ctrl.AuditCommand != "" {
			auditCmd := ctrl.AuditCommand
			if strings.Contains(auditCmd, "|") || strings.Contains(auditCmd, "for ") || strings.Contains(auditCmd, "do ") || strings.Contains(auditCmd, "if ") {
				// Shell command - execute via sh -c
				checkResult := controls.CheckCommandOutputEmptyWithControl("sh", []string{"-c", auditCmd}, ctrl.Description, ctrl.ID)
				result.Status = string(checkResult.Status)
				result.ActualValue = checkResult.ActualValue
				result.EvidenceCommand = checkResult.Evidence.Source + ": " + checkResult.Evidence.Snippet
			} else {
				// Simple command - parse normally
				parts := strings.Fields(auditCmd)
				if len(parts) > 0 {
					cmdName := parts[0]
					args := parts[1:]
					checkResult := controls.CheckCommandOutputEmptyWithControl(cmdName, args, ctrl.Description, ctrl.ID)
					result.Status = string(checkResult.Status)
					result.ActualValue = checkResult.ActualValue
					result.EvidenceCommand = checkResult.Evidence.Source + ": " + checkResult.Evidence.Snippet
				} else {
					result.Status = "ERROR"
					result.ActualValue = fmt.Sprintf("Unknown control type: %s (invalid audit_command)", ctrl.Type)
					result.EvidenceCommand = "N/A"
				}
			}
		// Strategy 4: FileExists (just file_path)
		} else if ctrl.FilePath != "" {
			checkResult := controls.CheckFileExists(ctrl.FilePath, ctrl.Description)
			result.Status = string(checkResult.Status)
			result.ActualValue = checkResult.ActualValue
			result.EvidenceCommand = checkResult.EvidenceCommand
		// Strategy 5: Try to extract from title/description for common patterns
		} else if strings.Contains(strings.ToLower(ctrl.Title), "kernel module") && ctrl.ModuleName == "" {
			// Try to extract module name from title (e.g., "Ensure cramfs kernel module is not available")
			// Extract word before "kernel module"
			words := strings.Fields(strings.ToLower(ctrl.Title))
			for i, word := range words {
				if word == "kernel" && i > 0 {
					moduleName := words[i-1]
					checkResult := controls.CheckKernelModule(moduleName, "not_available")
					result.Status = string(checkResult.Status)
					result.ActualValue = checkResult.ActualValue
					result.EvidenceCommand = checkResult.EvidenceCommand
					break
				}
			}
			if result.Status == "" {
				result.Status = "ERROR"
				result.ActualValue = fmt.Sprintf("Unknown control type: %s (cannot infer module name from title)", ctrl.Type)
				result.EvidenceCommand = "N/A"
			}
		} else {
			// Last resort: Mark as MANUAL if we can't figure it out
			result.Status = "MANUAL"
			result.ActualValue = fmt.Sprintf("Control type '%s' requires manual verification (no automated check available)", ctrl.Type)
			result.EvidenceCommand = "N/A"
		}
	}

	return result
}

func (s *Scanner) CountStatus(results []Result, status string) int {
	count := 0
	for _, r := range results {
		if r.Status == status {
			count++
		}
	}
	return count
}

// NormalizeStatus - eliminate SKIPPED and handle legacy statuses
func NormalizeStatus(status string) string {
	switch status {
	case "SKIPPED":
		return "NOT_APPLICABLE" // CIS compliance: no SKIPPED
	case "PASS", "FAIL", "MANUAL", "NOT_APPLICABLE", "ERROR":
		return status // Valid statuses
	default:
		return "ERROR" // Unknown status becomes ERROR
	}
}

// Helper functions for consistent status returns
func NotApplicableIf(condition bool, reason string) controls.CheckResult {
	if condition {
		return controls.NotApplicable(reason, "condition not met")
	}
	return controls.CheckResult{} // Continue with normal check
}

func NotApplicableForMissingPath(path string) controls.CheckResult {
	return controls.NotApplicable(fmt.Sprintf("Path %s does not exist", path), "file not found")
}

func getStatusSymbol(status string) string {
	status = NormalizeStatus(status) // Always normalize first
	switch status {
	case "PASS":
		return "✓"
	case "FAIL":
		return "✗"
	case "MANUAL":
		return "⚠"
	case "NOT_APPLICABLE":
		return "○"
	case "ERROR":
		return "✖"
	default:
		return "?"
	}
}

func truncate(s string, maxLen int) string {
	if len(s) <= maxLen {
		return s
	}
	return s[:maxLen-3] + "..."
}

func (s *Scanner) GenerateCSVReport(results []Result) error {
	reportResults := make([]report.Result, len(results))
	for i, r := range results {
		reportResults[i] = report.Result{
			ID:           r.ID,
			Title:        r.Title,
			Section:      r.Section,
			Status:       r.Status,
			CISReference: r.CISReference,
			Remediation:  r.Remediation,
			Description:  r.Description,
		}
	}
	return report.GenerateCSV(s.OutputDir, reportResults)
}

func (s *Scanner) GenerateHTMLReport(results []Result) error {
	reportResults := make([]report.Result, len(results))
	for i, r := range results {
		reportResults[i] = report.Result{
			ID:           r.ID,
			Title:        r.Title,
			Section:      r.Section,
			Status:       r.Status,
			CISReference: r.CISReference,
			Remediation:  r.Remediation,
			Description:  r.Description,
		}
	}
	return report.GenerateHTML(s.OutputDir, reportResults)
}
