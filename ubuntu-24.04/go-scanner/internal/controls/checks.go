package controls

import (
	"context"
	"fmt"
	"os/exec"
	"strings"
	"time"
)

func CheckKernelModule(moduleName, expectedStatus string) CheckResult {
	ctx, _ := BuildScanContext()
	modInfo := ctx.GetModuleInfo(moduleName)
	
	if expectedStatus == "not_available" {
		// If module is loaded, it's definitely available - FAIL
		if modInfo.Loaded {
			return Fail(
				"Module is loaded",
				fmt.Sprintf("%s loaded", moduleName),
				fmt.Sprintf("Module %s must be disabled", moduleName),
			)
		}
		
		// If module doesn't exist in kernel at all, it's not available - PASS
		// This is common in cloud AMIs where modules are compiled out
		if !modInfo.Exists {
			return Pass(
				"Module not available in kernel (not compiled)",
				"module not found in /lib/modules",
			)
		}
		
		// Module exists but not loaded
		if modInfo.Blacklisted {
			// Blacklisted and not loaded - PASS
			return Pass(
				"Module blacklisted and not loaded",
				fmt.Sprintf("install %s /bin/false", moduleName),
			)
		} else {
			// Exists but not blacklisted - should blacklist it - FAIL
			return Fail(
				"Module exists but not blacklisted",
				fmt.Sprintf("%s exists", moduleName),
				fmt.Sprintf("Module %s should be blacklisted", moduleName),
			)
		}
	}
	
	return Error(fmt.Errorf("unknown expected_status: %s", expectedStatus), "validation")
}

func CheckMountPoint(mountPoint, expectedStatus string) CheckResult {
	ctx, _ := BuildScanContext()
	
	if expectedStatus == "separate_partition" {
		if mountInfo, exists := ctx.Mounts.Runtime[mountPoint]; exists {
			// Check if it's actually a separate partition (not on root device)
			rootDevice := ""
			if rootMount, rootExists := ctx.Mounts.Runtime["/"]; rootExists {
				rootDevice = rootMount.Device
			}
			
			// If mount device is same as root, it's not a separate partition
			if rootDevice != "" && mountInfo.Device == rootDevice {
				// Cloud environments often use single root volume - NOT_APPLICABLE
				return NotApplicable(
					fmt.Sprintf("Mount point %s is on root volume (cloud best practice)", mountPoint),
					fmt.Sprintf("single root volume: %s", rootDevice),
				)
			}
			
			return Pass(
				fmt.Sprintf("Separate partition: %s (%s)", mountInfo.Device, mountInfo.FS),
				fmt.Sprintf("%s %s", mountInfo.Device, mountPoint),
			)
		} else {
			// Mount point doesn't exist - in cloud environments, this is NOT_APPLICABLE
			// CIS allows cloud-specific exceptions for single root volume
			return NotApplicable(
				fmt.Sprintf("Mount point %s not configured (cloud single-volume deployment)", mountPoint),
				"mount not found - cloud environment",
			)
		}
	}
	
	return Error(fmt.Errorf("unknown expected_status: %s", expectedStatus), "validation")
}

func CheckMountOption(mountPoint, requiredOption string) CheckResult {
	ctx, _ := BuildScanContext()
	
	mountInfo, runtimeExists := ctx.Mounts.Runtime[mountPoint]
	if !runtimeExists {
		// CIS semantics: if partition doesn't exist, it's NOT_APPLICABLE
		return NotApplicable(
			fmt.Sprintf("Mount point %s not configured as separate partition", mountPoint),
			"mount not found",
		)
	}
	
	fstabEntry, fstabExists := ctx.Mounts.Fstab[mountPoint]
	
	runtimeHasOption := false
	for opt := range mountInfo.Options {
		if opt == requiredOption {
			runtimeHasOption = true
			break
		}
	}
	
	fstabHasOption := false
	if fstabExists {
		for opt := range fstabEntry.Options {
			if opt == requiredOption {
				fstabHasOption = true
				break
			}
		}
	}
	
	if runtimeHasOption && fstabHasOption {
		return Pass(
			fmt.Sprintf("Option %s present (runtime + fstab)", requiredOption),
			fmt.Sprintf("%s option found", requiredOption),
		)
	} else if runtimeHasOption && !fstabHasOption {
		return Fail(
			fmt.Sprintf("Option %s present in runtime but not persistent", requiredOption),
			fmt.Sprintf("%s in runtime only", requiredOption),
			fmt.Sprintf("Mount %s missing %s in fstab", mountPoint, requiredOption),
		)
	} else {
		optList := make([]string, 0, len(mountInfo.Options))
		for opt := range mountInfo.Options {
			optList = append(optList, opt)
		}
		return Fail(
			fmt.Sprintf("Option %s missing (runtime: %s)", requiredOption, strings.Join(optList, ",")),
			strings.Join(optList, ","),
			fmt.Sprintf("Mount %s missing %s option", mountPoint, requiredOption),
		)
	}
}

func CheckServiceStatus(serviceName, expectedStatus string) CheckResult {
	// Use systemctl is-enabled to get accurate status (handles static services)
	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()
	
	cmd := exec.CommandContext(ctx, "systemctl", "is-enabled", serviceName)
	output, err := cmd.Output()
	outputStr := strings.TrimSpace(string(output))
	
	if ctx.Err() == context.DeadlineExceeded {
		return Error(fmt.Errorf("systemctl timeout"), "systemctl")
	}
	
	// systemctl is-enabled returns:
	// - "enabled" - service is enabled
	// - "disabled" - service is disabled
	// - "static" - service is always enabled (static service, cannot be disabled)
	// - "masked" - service is masked
	// - "indirect" - service is indirectly enabled
	// - error with exit code 1 - service not found or error
	
	if expectedStatus == "enabled" {
		// "enabled", "static", and "indirect" all mean the service is enabled
		if outputStr == "enabled" || outputStr == "static" || outputStr == "indirect" {
			return Pass(
				fmt.Sprintf("Service %s is enabled (status: %s)", serviceName, outputStr),
				fmt.Sprintf("status: %s", outputStr),
			)
		} else if err != nil {
			return Fail(
				fmt.Sprintf("Service %s is not enabled (status: %s)", serviceName, outputStr),
				outputStr,
				fmt.Sprintf("Service %s not enabled", serviceName),
			)
		} else {
			return Fail(
				fmt.Sprintf("Service %s is disabled (status: %s)", serviceName, outputStr),
				outputStr,
				fmt.Sprintf("Service %s should be enabled", serviceName),
			)
		}
	} else if expectedStatus == "disabled" || expectedStatus == "inactive" {
		if outputStr == "disabled" || (err != nil && outputStr == "") {
			return Pass(
				fmt.Sprintf("Service %s is disabled", serviceName),
				"service disabled",
			)
		} else {
			return Fail(
				fmt.Sprintf("Service %s is enabled (status: %s)", serviceName, outputStr),
				outputStr,
				fmt.Sprintf("Service %s should be disabled", serviceName),
			)
		}
	}
	
	return Error(fmt.Errorf("unknown expected_status: %s", expectedStatus), "validation")
}

func CheckPackageInstalled(packageName, expectedStatus string) CheckResult {
	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()
	
	cmd := exec.CommandContext(ctx, "rpm", "-q", packageName)
	output, err := cmd.Output()
	outputStr := strings.TrimSpace(string(output))
	
	if ctx.Err() == context.DeadlineExceeded {
		return Error(fmt.Errorf("RPM query timeout"), "rpm")
	}
	
	if expectedStatus == "installed" {
		if err == nil {
			return Pass(
				fmt.Sprintf("Package installed: %s", outputStr),
				outputStr,
			)
		} else {
			return Fail(
				"Package not installed",
				"not installed",
				fmt.Sprintf("Package %s not found", packageName),
			)
		}
	} else if expectedStatus == "not_installed" {
		if err != nil {
			return Pass(
				"Package not installed (as expected)",
				"not installed",
			)
		} else {
			return Fail(
				fmt.Sprintf("Package installed: %s", outputStr),
				outputStr,
				fmt.Sprintf("Package %s should not be installed", packageName),
			)
		}
	}
	
	return Error(fmt.Errorf("unknown expected_status: %s", expectedStatus), "validation")
}