package scanner

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"

	"github.com/vijenex/linux-cis-scanner/rhel-8/internal/controls"
	"github.com/vijenex/linux-cis-scanner/rhel-8/internal/report"
)

type Scanner struct {
	OutputDir  string
	Profile    string
	Milestones []Milestone
}

type Milestone struct {
	ID          string            `json:"milestone"`
	Section     string            `json:"section"`
	Description string            `json:"description"`
	Controls    []controls.Control `json:"controls"`
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

	for _, milestone := range s.Milestones {
		fmt.Printf("📄 Processing %s...\n", milestone.ID)

		for _, ctrl := range milestone.Controls {
			// Skip non-automated controls
			if !ctrl.Automated {
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
			
			// Skip Level 2 controls if running Level 1 profile
			if s.Profile == "Level1" && ctrl.Profile == "Level2" {
				results = append(results, Result{
					ID:          ctrl.ID,
					Title:       ctrl.Title,
					Section:     ctrl.Section,
					Status:      "SKIPPED",
					CISReference: ctrl.CISReference,
					Remediation: ctrl.Remediation,
					Description: fmt.Sprintf("Skipped (Profile: %s)", ctrl.Profile),
				})
				continue
			}

			// Execute control
			result := s.executeControl(ctrl)
			results = append(results, result)

			// Print status
			statusSymbol := getStatusSymbol(result.Status)
			fmt.Printf("  %s %s: %s\n", statusSymbol, ctrl.ID, truncate(ctrl.Title, 60))
		}
	}

	return results
}

func (s *Scanner) executeControl(ctrl controls.Control) Result {
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
		result.Status = checkResult.Status
		result.ActualValue = checkResult.ActualValue
		result.EvidenceCommand = checkResult.EvidenceCommand
		// Keep original CIS description, don't overwrite

	case "MountPoint":
		checkResult := controls.CheckMountPoint(ctrl.MountPoint, ctrl.ExpectedStatus)
		result.Status = checkResult.Status
		result.ActualValue = checkResult.ActualValue
		result.EvidenceCommand = checkResult.EvidenceCommand

	case "MountOption":
		checkResult := controls.CheckMountOption(ctrl.MountPoint, ctrl.RequiredOption)
		result.Status = checkResult.Status
		result.ActualValue = checkResult.ActualValue
		result.EvidenceCommand = checkResult.EvidenceCommand

	case "ServiceStatus":
		checkResult := controls.CheckServiceStatus(ctrl.ServiceName, ctrl.ExpectedStatus)
		result.Status = checkResult.Status
		result.ActualValue = checkResult.ActualValue
		result.EvidenceCommand = checkResult.EvidenceCommand

	case "PackageInstalled":
		checkResult := controls.CheckPackageInstalled(ctrl.PackageName, ctrl.ExpectedStatus)
		result.Status = checkResult.Status
		result.ActualValue = checkResult.ActualValue
		result.EvidenceCommand = checkResult.EvidenceCommand

	case "PackageNotInstalled":
		checkResult := controls.CheckPackageInstalled(ctrl.PackageName, "not_installed")
		result.Status = checkResult.Status
		result.ActualValue = checkResult.ActualValue
		result.EvidenceCommand = checkResult.EvidenceCommand

	case "SysctlParameter":
		// Support both parameter_name and parameter fields
		paramName := ctrl.ParameterName
		if paramName == "" {
			paramName = ctrl.Parameter
		}
		checkResult := controls.CheckSysctlParameter(paramName, ctrl.ExpectedValue)
		result.Status = checkResult.Status
		result.ActualValue = checkResult.ActualValue
		result.EvidenceCommand = checkResult.EvidenceCommand

	case "FilePermissions":
		checkResult := controls.CheckFilePermissions(ctrl.FilePath, ctrl.ExpectedPermissions, ctrl.ExpectedOwner, ctrl.ExpectedGroup)
		result.Status = checkResult.Status
		result.ActualValue = checkResult.ActualValue
		result.EvidenceCommand = checkResult.EvidenceCommand

	case "FileContent":
		checkResult := controls.CheckFileContent(ctrl.FilePath, ctrl.Pattern, ctrl.ExpectedResult)
		result.Status = checkResult.Status
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

func getStatusSymbol(status string) string {
	switch status {
	case "PASS":
		return "✓"
	case "FAIL":
		return "✗"
	case "MANUAL":
		return "⚠"
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
