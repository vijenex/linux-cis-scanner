package controls

type Control struct {
	ID             string `json:"id"`
	Title          string `json:"title"`
	Section        string `json:"section"`
	Type           string `json:"type"`
	Profile        string `json:"profile"`
	Automated      bool   `json:"automated"`
	CISReference   string `json:"cis_reference"`
	Description    string `json:"description"`
	Remediation    string `json:"remediation"`
	
	// Type-specific fields
	ModuleName     string `json:"module_name,omitempty"`
	MountPoint     string `json:"mount_point,omitempty"`
	RequiredOption string `json:"required_option,omitempty"`
	ServiceName    string `json:"service_name,omitempty"`
	PackageName    string `json:"package_name,omitempty"`
	ExpectedStatus string `json:"expected_status,omitempty"`
	ParameterName      string `json:"parameter_name,omitempty"`
	ExpectedValue      string `json:"expected_value,omitempty"`
	FilePath           string `json:"file_path,omitempty"`
	ExpectedPermissions string `json:"expected_permissions,omitempty"`
	ExpectedOwner      string `json:"expected_owner,omitempty"`
	ExpectedGroup      string `json:"expected_group,omitempty"`
	Pattern            string `json:"pattern,omitempty"`
	ExpectedResult     string `json:"expected_result,omitempty"`
}

type CheckResult struct {
	Status          string
	ActualValue     string
	EvidenceCommand string
	Description     string
}
