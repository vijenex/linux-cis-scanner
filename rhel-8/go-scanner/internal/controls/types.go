package controls

type Control struct {
	ID             string `json:"id"`
	Title          string `json:"title"`
	Section        string `json:"section"`
	Type           string `json:"type"`
	Profile        string `json:"profile"`
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
	ParameterName  string `json:"parameter_name,omitempty"`
	ExpectedValue  string `json:"expected_value,omitempty"`
}

type CheckResult struct {
	Status          string
	ActualValue     string
	EvidenceCommand string
	Description     string
}
