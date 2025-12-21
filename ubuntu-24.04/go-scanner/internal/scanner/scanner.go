package scanner

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"strings"

	"github.com/vijenex/linux-cis-scanner/ubuntu-24.04/internal/controls"
	"github.com/vijenex/linux-cis-scanner/ubuntu-24.04/internal/report"
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
			
			// Handle missing "automated" field - if missing, infer from type
			// Most control types are automated, except "Manual" type
			isAutomated := ctrl.Automated
			if !isAutomated && ctrl.Type != "Manual" {
				// If automated field is missing but type is not "Manual", assume automated
				// This handles legacy milestone files without "automated" field
				isAutomated = true
			}
			
			// Skip non-automated controls
			if !isAutomated || ctrl.Type == "Manual" {
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

	case "ServiceStatus":
		checkResult := controls.CheckServiceStatus(ctrl.ServiceName, ctrl.ExpectedStatus)
		result.Status = string(checkResult.Status)
		result.ActualValue = checkResult.ActualValue
		result.EvidenceCommand = checkResult.EvidenceCommand

	case "PackageInstalled":
		checkResult := controls.CheckPackageInstalled(ctrl.PackageName, ctrl.ExpectedStatus)
		result.Status = string(checkResult.Status)
		result.ActualValue = checkResult.ActualValue
		result.EvidenceCommand = checkResult.EvidenceCommand

	case "PackageNotInstalled":
		checkResult := controls.CheckPackageInstalled(ctrl.PackageName, "not_installed")
		result.Status = string(checkResult.Status)
		result.ActualValue = checkResult.ActualValue
		result.EvidenceCommand = checkResult.EvidenceCommand

	case "SysctlParameter":
		// Support both parameter_name and parameter fields
		paramName := ctrl.ParameterName
		if paramName == "" {
			paramName = ctrl.Parameter
		}
		checkResult := controls.CheckSysctlParameter(paramName, ctrl.ExpectedValue)
		result.Status = string(checkResult.Status)
		result.ActualValue = checkResult.ActualValue
		result.EvidenceCommand = checkResult.EvidenceCommand

	case "FilePermissions":
		checkResult := controls.CheckFilePermissions(ctrl.FilePath, ctrl.ExpectedPermissions, ctrl.ExpectedOwner, ctrl.ExpectedGroup)
		result.Status = string(checkResult.Status)
		result.ActualValue = checkResult.ActualValue
		result.EvidenceCommand = checkResult.EvidenceCommand

	case "FileContent":
		checkResult := controls.CheckFileContent(ctrl.FilePath, ctrl.Pattern, ctrl.ExpectedResult)
		result.Status = string(checkResult.Status)
		result.ActualValue = checkResult.ActualValue
		result.EvidenceCommand = checkResult.EvidenceCommand

	case "SSHConfig":
		checkResult := controls.CheckSSHConfig(ctrl.Parameter, ctrl.ExpectedValue, ctrl.Description)
		result.Status = string(checkResult.Status)
		result.ActualValue = checkResult.ActualValue
		result.EvidenceCommand = checkResult.EvidenceCommand

	case "PAMConfig":
		checkResult := controls.CheckPAMConfig(ctrl.FilePath, ctrl.ModuleName, ctrl.Parameter, ctrl.ExpectedValue, ctrl.Description)
		result.Status = string(checkResult.Status)
		result.ActualValue = checkResult.ActualValue
		result.EvidenceCommand = checkResult.EvidenceCommand

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

	default:
		result.Status = "MANUAL"
		result.ActualValue = "Manual verification required"
		result.EvidenceCommand = "N/A"
		result.Description = "This control requires manual verification"
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
