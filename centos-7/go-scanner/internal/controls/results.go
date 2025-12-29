package controls

import "fmt"

// Status normalization - no more string chaos
func Pass(actual, evidence string) CheckResult {
	return CheckResult{
		Status:          StatusPass,
		ActualValue:     actual,
		Evidence:        Evidence{Method: "parsed", Source: "system", Snippet: evidence},
		EvidenceCommand: evidence, // Backward compatibility
		Description:     "Control passed",
	}
}

func Fail(actual, evidence, reason string) CheckResult {
	return CheckResult{
		Status:          StatusFail,
		ActualValue:     actual,
		Evidence:        Evidence{Method: "parsed", Source: "system", Snippet: evidence},
		EvidenceCommand: evidence, // Backward compatibility
		Description:     reason,
	}
}

func NotApplicable(reason, evidence string) CheckResult {
	return CheckResult{
		Status:          StatusNotApplicable,
		ActualValue:     reason,
		Evidence:        Evidence{Method: "system", Source: "config", Snippet: evidence},
		EvidenceCommand: evidence, // Backward compatibility
		Description:     "Control not applicable: " + reason,
	}
}

func Error(err error, source string) CheckResult {
	errMsg := err.Error()
	return CheckResult{
		Status:          StatusError,
		ActualValue:     errMsg,
		Evidence:        Evidence{Method: "error", Source: source, Snippet: errMsg},
		EvidenceCommand: fmt.Sprintf("%s: %s", source, errMsg), // Backward compatibility
		Description:     "Control execution failed",
	}
}

func ValidationError(controlID, field, reason string) CheckResult {
	return CheckResult{
		Status:      StatusError,
		ActualValue: fmt.Sprintf("Invalid %s: %s", field, reason),
		Evidence:    Evidence{Method: "validation", Source: controlID, Snippet: field},
		Description: "Control validation failed",
	}
}

