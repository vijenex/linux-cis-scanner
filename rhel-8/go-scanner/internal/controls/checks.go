package controls

import (
	"bufio"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"regexp"
	"strings"
)

func CheckKernelModule(moduleName, expectedStatus string) CheckResult {
	// Check if module is blacklisted
	blacklisted := false
	modprobeDirs := []string{"/etc/modprobe.d/", "/lib/modprobe.d/", "/usr/lib/modprobe.d/"}
	
	for _, dir := range modprobeDirs {
		files, err := filepath.Glob(filepath.Join(dir, "*.conf"))
		if err != nil {
			continue
		}
		
		for _, file := range files {
			content, err := os.ReadFile(file)
			if err != nil {
				continue
			}
			
			pattern := fmt.Sprintf(`install\s+%s\s+/bin/(true|false)`, regexp.QuoteMeta(moduleName))
			matched, _ := regexp.Match(pattern, content)
			if matched {
				blacklisted = true
				break
			}
		}
		if blacklisted {
			break
		}
	}
	
	// Check if module is loaded (handle both hyphen and underscore)
	loaded := false
	moduleNameUnderscore := strings.ReplaceAll(moduleName, "-", "_")
	cmd := exec.Command("lsmod")
	output, err := cmd.Output()
	if err == nil {
		loaded = strings.Contains(string(output), moduleName) || strings.Contains(string(output), moduleNameUnderscore)
	}
	
	// Check if module exists (try both hyphen and underscore)
	cmd = exec.Command("modinfo", moduleName)
	moduleExists := cmd.Run() == nil
	if !moduleExists {
		cmd = exec.Command("modinfo", moduleNameUnderscore)
		moduleExists = cmd.Run() == nil
	}
	
	if expectedStatus == "not_available" {
		if blacklisted && !loaded {
			return CheckResult{
				Status:          "PASS",
				ActualValue:     "Module blacklisted and not loaded",
				EvidenceCommand: fmt.Sprintf("lsmod | grep %s; modprobe -n -v %s", moduleName, moduleName),
				Description:     fmt.Sprintf("Module %s: blacklisted=%t, loaded=%t", moduleName, blacklisted, loaded),
			}
		} else if !moduleExists {
			return CheckResult{
				Status:          "PASS",
				ActualValue:     "Module not available in kernel",
				EvidenceCommand: fmt.Sprintf("modinfo %s", moduleName),
				Description:     fmt.Sprintf("Module %s not found in kernel", moduleName),
			}
		} else if loaded {
			return CheckResult{
				Status:          "FAIL",
				ActualValue:     "Module is loaded",
				EvidenceCommand: fmt.Sprintf("lsmod | grep %s", moduleName),
				Description:     fmt.Sprintf("Module %s is currently loaded", moduleName),
			}
		} else {
			return CheckResult{
				Status:          "FAIL",
				ActualValue:     "Module available but not blacklisted",
				EvidenceCommand: fmt.Sprintf("modprobe -n -v %s", moduleName),
				Description:     fmt.Sprintf("Module %s exists but not blacklisted", moduleName),
			}
		}
	}
	
	return CheckResult{
		Status:          "FAIL",
		ActualValue:     fmt.Sprintf("Unexpected expected_status: %s", expectedStatus),
		EvidenceCommand: "N/A",
		Description:     "Invalid expected status",
	}
}

func CheckMountPoint(mountPoint, expectedStatus string) CheckResult {
	file, err := os.Open("/proc/mounts")
	if err != nil {
		return CheckResult{
			Status:          "ERROR",
			ActualValue:     "Cannot access mount information",
			EvidenceCommand: "findmnt",
			Description:     "Access to /proc/mounts denied",
		}
	}
	defer file.Close()
	
	mountFound := false
	deviceInfo := ""
	
	scanner := bufio.NewScanner(file)
	for scanner.Scan() {
		parts := strings.Fields(scanner.Text())
		if len(parts) >= 2 && parts[1] == mountPoint {
			mountFound = true
			deviceInfo = parts[0]
			break
		}
	}
	
	if expectedStatus == "separate_partition" {
		if mountFound && !strings.HasPrefix(deviceInfo, "/dev/loop") {
			return CheckResult{
				Status:          "PASS",
				ActualValue:     fmt.Sprintf("Separate partition: %s", deviceInfo),
				EvidenceCommand: fmt.Sprintf("findmnt %s", mountPoint),
				Description:     fmt.Sprintf("Mount point %s verification", mountPoint),
			}
		} else if mountFound {
			return CheckResult{
				Status:          "PASS",
				ActualValue:     fmt.Sprintf("Mounted: %s", deviceInfo),
				EvidenceCommand: fmt.Sprintf("findmnt %s", mountPoint),
				Description:     fmt.Sprintf("Mount point %s is mounted", mountPoint),
			}
		} else {
			return CheckResult{
				Status:          "FAIL",
				ActualValue:     "Not a separate partition",
				EvidenceCommand: fmt.Sprintf("findmnt %s", mountPoint),
				Description:     fmt.Sprintf("Mount point %s not found", mountPoint),
			}
		}
	}
	
	return CheckResult{
		Status:          "FAIL",
		ActualValue:     fmt.Sprintf("Unexpected expected_status: %s", expectedStatus),
		EvidenceCommand: "N/A",
		Description:     "Invalid expected status",
	}
}

func CheckMountOption(mountPoint, requiredOption string) CheckResult {
	file, err := os.Open("/proc/mounts")
	if err != nil {
		return CheckResult{
			Status:          "ERROR",
			ActualValue:     "Cannot access mount information",
			EvidenceCommand: fmt.Sprintf("findmnt %s", mountPoint),
			Description:     "Access to /proc/mounts denied",
		}
	}
	defer file.Close()
	
	mountFound := false
	var options []string
	
	scanner := bufio.NewScanner(file)
	for scanner.Scan() {
		parts := strings.Fields(scanner.Text())
		if len(parts) >= 4 && parts[1] == mountPoint {
			mountFound = true
			options = strings.Split(parts[3], ",")
			break
		}
	}
	
	if !mountFound {
		return CheckResult{
			Status:          "FAIL",
			ActualValue:     "Mount point not found",
			EvidenceCommand: fmt.Sprintf("findmnt %s", mountPoint),
			Description:     fmt.Sprintf("Mount point %s is not mounted", mountPoint),
		}
	}
	
	optionPresent := false
	for _, opt := range options {
		if opt == requiredOption {
			optionPresent = true
			break
		}
	}
	
	status := "FAIL"
	if optionPresent {
		status = "PASS"
	}
	
	return CheckResult{
		Status:          status,
		ActualValue:     fmt.Sprintf("Options: %s", strings.Join(options, ",")),
		EvidenceCommand: fmt.Sprintf("findmnt -n %s | grep -v %s", mountPoint, requiredOption),
		Description:     fmt.Sprintf("Mount %s: %s %s", mountPoint, requiredOption, map[bool]string{true: "found", false: "missing"}[optionPresent]),
	}
}

func CheckServiceStatus(serviceName, expectedStatus string) CheckResult {
	cmd := exec.Command("systemctl", "is-enabled", serviceName)
	output, err := cmd.Output()
	outputStr := strings.TrimSpace(string(output))
	
	if expectedStatus == "enabled" {
		if err == nil && strings.Contains(outputStr, "enabled") {
			return CheckResult{
				Status:          "PASS",
				ActualValue:     fmt.Sprintf("Service %s is enabled", serviceName),
				EvidenceCommand: fmt.Sprintf("systemctl is-enabled %s", serviceName),
				Description:     fmt.Sprintf("Service %s status check", serviceName),
			}
		} else {
			return CheckResult{
				Status:          "FAIL",
				ActualValue:     fmt.Sprintf("Service %s is not enabled: %s", serviceName, outputStr),
				EvidenceCommand: fmt.Sprintf("systemctl is-enabled %s", serviceName),
				Description:     fmt.Sprintf("Service %s status check", serviceName),
			}
		}
	} else if expectedStatus == "disabled" {
		if err != nil || strings.Contains(outputStr, "disabled") || strings.Contains(outputStr, "masked") {
			return CheckResult{
				Status:          "PASS",
				ActualValue:     fmt.Sprintf("Service %s is disabled/masked", serviceName),
				EvidenceCommand: fmt.Sprintf("systemctl is-enabled %s", serviceName),
				Description:     fmt.Sprintf("Service %s status check", serviceName),
			}
		} else {
			return CheckResult{
				Status:          "FAIL",
				ActualValue:     fmt.Sprintf("Service %s is enabled", serviceName),
				EvidenceCommand: fmt.Sprintf("systemctl is-enabled %s", serviceName),
				Description:     fmt.Sprintf("Service %s status check", serviceName),
			}
		}
	}
	
	return CheckResult{
		Status:          "FAIL",
		ActualValue:     fmt.Sprintf("Unknown expected_status: %s", expectedStatus),
		EvidenceCommand: "N/A",
		Description:     "Invalid expected status",
	}
}

func CheckPackageInstalled(packageName, expectedStatus string) CheckResult {
	cmd := exec.Command("rpm", "-q", packageName)
	output, err := cmd.Output()
	outputStr := strings.TrimSpace(string(output))
	
	if expectedStatus == "installed" {
		if err == nil {
			return CheckResult{
				Status:          "PASS",
				ActualValue:     fmt.Sprintf("Package %s is installed: %s", packageName, outputStr),
				EvidenceCommand: fmt.Sprintf("rpm -q %s", packageName),
				Description:     fmt.Sprintf("Package %s installation check", packageName),
			}
		} else {
			return CheckResult{
				Status:          "FAIL",
				ActualValue:     fmt.Sprintf("Package %s is not installed", packageName),
				EvidenceCommand: fmt.Sprintf("rpm -q %s", packageName),
				Description:     fmt.Sprintf("Package %s installation check", packageName),
			}
		}
	} else if expectedStatus == "not_installed" {
		if err != nil {
			return CheckResult{
				Status:          "PASS",
				ActualValue:     fmt.Sprintf("Package %s is not installed", packageName),
				EvidenceCommand: fmt.Sprintf("rpm -q %s", packageName),
				Description:     fmt.Sprintf("Package %s installation check", packageName),
			}
		} else {
			return CheckResult{
				Status:          "FAIL",
				ActualValue:     fmt.Sprintf("Package %s is installed: %s", packageName, outputStr),
				EvidenceCommand: fmt.Sprintf("rpm -q %s", packageName),
				Description:     fmt.Sprintf("Package %s installation check", packageName),
			}
		}
	}
	
	return CheckResult{
		Status:          "FAIL",
		ActualValue:     fmt.Sprintf("Unknown expected_status: %s", expectedStatus),
		EvidenceCommand: "N/A",
		Description:     "Invalid expected status",
	}
}
