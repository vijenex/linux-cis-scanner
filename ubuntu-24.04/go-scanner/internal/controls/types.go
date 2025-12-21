package controls

import (
	"encoding/json"
	"fmt"
)

// Status types - strongly typed to prevent errors
type Status string

const (
	StatusPass          Status = "PASS"
	StatusFail          Status = "FAIL"
	StatusManual        Status = "MANUAL"
	StatusNotApplicable Status = "NOT_APPLICABLE"
	StatusError         Status = "ERROR"
)

// Evidence - audit-safe evidence collection
type Evidence struct {
	Method  string `json:"method"`  // "file", "proc", "parsed", "command"
	Source  string `json:"source"`  // path or tool name
	Snippet string `json:"snippet"` // actual evidence
}

// Control metadata (separated from check logic)
type ControlMetadata struct {
	ID           string `json:"id"`
	Title        string `json:"title"`
	Section      string `json:"section"`
	Profile      string `json:"profile"`
	Automated    bool   `json:"automated"`
	CISReference string `json:"cis_reference"`
	Description  string `json:"description"`
	Remediation  string `json:"remediation"`
}

// Control - clean separation of metadata and check logic
type Control struct {
	ControlMetadata
	Type  string          `json:"type"`
	Check json.RawMessage `json:"check"`
}

// Legacy Control for backward compatibility
type LegacyControl struct {
	ID             string `json:"id"`
	Title          string `json:"title"`
	Section        string `json:"section"`
	Type           string `json:"type"`
	Profile        string `json:"profile"`
	Automated      *bool  `json:"automated,omitempty"` // Pointer to detect missing vs false
	CISReference   string `json:"cis_reference"`
	Description    string `json:"description"`
	Remediation    string `json:"remediation"`
	
	// Legacy fields - will be migrated
	ModuleName          string   `json:"module_name,omitempty"`
	MountPoint          string   `json:"mount_point,omitempty"`
	RequiredOption      string   `json:"required_option,omitempty"`
	ServiceName         string   `json:"service_name,omitempty"`
	ServiceNames        []string `json:"service_names,omitempty"` // Array variant for ServiceNotInUse
	PackageName         string   `json:"package_name,omitempty"`
	Package             string   `json:"package,omitempty"`        // Alternative field name
	PackageNames        []string `json:"package_names,omitempty"`  // Array variant
	ExpectedStatus      string   `json:"expected_status,omitempty"`
	ExpectedState       string   `json:"expected_state,omitempty"` // Alternative field name
	ShouldBeInstalled   *bool    `json:"should_be_installed,omitempty"` // Boolean variant
	ParameterName       string   `json:"parameter_name,omitempty"`
	Parameter           string   `json:"parameter,omitempty"`
	ExpectedValue       string   `json:"expected_value,omitempty"`
	FilePath            string   `json:"file_path,omitempty"`
	PasswdFile          string   `json:"passwd_file,omitempty"` // Alternative field name for /etc/passwd checks
	ShadowFile          string   `json:"shadow_file,omitempty"` // Alternative field name for /etc/shadow checks
	LogDirectory        string   `json:"log_directory,omitempty"` // Alternative field name for log directory checks
	ExpectedPermissions string   `json:"expected_permissions,omitempty"`
	ExpectedFilePerms   string   `json:"expected_file_permissions,omitempty"` // For LogFilePermissions
	ExpectedDirPerms    string   `json:"expected_dir_permissions,omitempty"` // For LogFilePermissions
	ExpectedOwner       string   `json:"expected_owner,omitempty"`
	ExpectedGroup       string   `json:"expected_group,omitempty"`
	Pattern             string   `json:"pattern,omitempty"`
	ExpectedResult      string   `json:"expected_result,omitempty"`
	AuditCommand        string   `json:"audit_command,omitempty"` // DEPRECATED - never execute
}

// Typed CheckSpecs - one per control type
type SysctlCheckSpec struct {
	Parameter string `json:"parameter"`
	Expected  string `json:"expected"`
}

type SSHCheckSpec struct {
	Parameter string `json:"parameter"`
	Expected  string `json:"expected"`
}

type PAMCheckSpec struct {
	File      string `json:"file"`
	Type      string `json:"pam_type"`
	Module    string `json:"module"`
	Parameter string `json:"parameter"`
	Expected  string `json:"expected"`
}

type ServiceCheckSpec struct {
	Name     string `json:"name"`
	Expected string `json:"expected"` // "enabled", "disabled", "active", "inactive"
}

type PackageCheckSpec struct {
	Name     string `json:"name"`
	Expected string `json:"expected"` // "installed", "not_installed"
}

type FilePermCheckSpec struct {
	Path        string `json:"path"`
	Permissions string `json:"permissions"`
	Owner       string `json:"owner"`
	Group       string `json:"group"`
}

type FileContentCheckSpec struct {
	Path     string `json:"path"`
	Pattern  string `json:"pattern"`
	Expected string `json:"expected"` // "found", "not_found"
}

type MountCheckSpec struct {
	Point    string `json:"point"`
	Expected string `json:"expected"` // "separate_partition"
}

type MountOptionCheckSpec struct {
	Point  string `json:"point"`
	Option string `json:"option"`
}

type KernelModuleCheckSpec struct {
	Module   string `json:"module"`
	Expected string `json:"expected"` // "not_available"
}

// CheckResult - strongly typed
type CheckResult struct {
	Status          Status
	ActualValue     string
	EvidenceCommand string   // Backward compatibility for pam.go/sudo.go
	Evidence        Evidence
	Description     string
}

// Normalize legacy controls for backward compatibility
func (lc *LegacyControl) Normalize() {
	// Normalize parameter fields
	if lc.ParameterName == "" {
		lc.ParameterName = lc.Parameter
	}
	
	// Normalize package fields - handle "package" -> "package_name"
	if lc.PackageName == "" && lc.Package != "" {
		lc.PackageName = lc.Package
	}
	// Handle package_names array - use first element
	if lc.PackageName == "" && len(lc.PackageNames) > 0 {
		lc.PackageName = lc.PackageNames[0]
	}
	
	// Normalize service fields - handle "service_names" array -> "service_name"
	if lc.ServiceName == "" && len(lc.ServiceNames) > 0 {
		lc.ServiceName = lc.ServiceNames[0]
	}
	
	// Normalize expected_status from expected_state
	if lc.ExpectedStatus == "" && lc.ExpectedState != "" {
		lc.ExpectedStatus = lc.ExpectedState
	}
	// Handle should_be_installed boolean -> expected_status
	if lc.ExpectedStatus == "" && lc.ShouldBeInstalled != nil {
		if *lc.ShouldBeInstalled {
			lc.ExpectedStatus = "installed"
		} else {
			lc.ExpectedStatus = "not_installed"
		}
	}
	
	// Normalize passwd_file -> file_path (for controls that use passwd_file)
	if lc.FilePath == "" && lc.PasswdFile != "" {
		lc.FilePath = lc.PasswdFile
	}
	// Normalize shadow_file -> file_path (for controls that use shadow_file)
	if lc.FilePath == "" && lc.ShadowFile != "" {
		lc.FilePath = lc.ShadowFile
	}
	// Normalize log_directory -> file_path (for LogFilePermissions)
	if lc.FilePath == "" && lc.LogDirectory != "" {
		lc.FilePath = lc.LogDirectory
	}
	// Normalize expected_file_permissions -> expected_permissions (for LogFilePermissions)
	if lc.ExpectedPermissions == "" && lc.ExpectedFilePerms != "" {
		lc.ExpectedPermissions = lc.ExpectedFilePerms
	}
}

// Validate control before execution
// Note: This should be called AFTER Normalize() has been called on the control
func (lc LegacyControl) Validate() error {
	switch lc.Type {
	case "SysctlParameter", "KernelParameter", "MultiKernelParameter":
		if lc.ParameterName == "" || lc.ExpectedValue == "" {
			return fmt.Errorf("missing parameter_name or expected_value for %s", lc.ID)
		}
	case "ServiceStatus", "Service", "ServiceNotInUse":
		// For ServiceNotInUse, check both service_name and service_names
		serviceName := lc.ServiceName
		if serviceName == "" && len(lc.ServiceNames) > 0 {
			serviceName = lc.ServiceNames[0]
		}
		if serviceName == "" {
			return fmt.Errorf("missing service_name or service_names for %s", lc.ID)
		}
		// ExpectedStatus is optional for ServiceNotInUse (defaults to "disabled")
		if lc.Type != "ServiceNotInUse" && lc.ExpectedStatus == "" {
			return fmt.Errorf("missing expected_status for %s", lc.ID)
		}
	case "PackageInstalled", "PackageNotInstalled", "Package", "MultiPackage":
		// Check all possible package field names
		packageName := lc.PackageName
		if packageName == "" && lc.Package != "" {
			packageName = lc.Package
		}
		if packageName == "" && len(lc.PackageNames) > 0 {
			packageName = lc.PackageNames[0]
		}
		if packageName == "" {
			return fmt.Errorf("missing package_name, package, or package_names for %s", lc.ID)
		}
	case "FilePermissions", "FilePermission", "SSHPrivateKeys", "SSHPublicKeys", "LogFilePermissions":
		if lc.FilePath == "" {
			return fmt.Errorf("missing file_path for %s", lc.ID)
		}
	case "FileContent", "ConfigFile":
		if lc.FilePath == "" || lc.Pattern == "" {
			return fmt.Errorf("missing file_path or pattern for %s", lc.ID)
		}
	case "MountPoint":
		if lc.MountPoint == "" {
			return fmt.Errorf("missing mount_point for %s", lc.ID)
		}
	case "MountOption":
		if lc.MountPoint == "" || lc.RequiredOption == "" {
			return fmt.Errorf("missing mount_point or required_option for %s", lc.ID)
		}
	case "KernelModule":
		if lc.ModuleName == "" {
			return fmt.Errorf("missing module_name for %s", lc.ID)
		}
	// For other types, validation is lenient - let execution handle it
	}
	return nil
}
