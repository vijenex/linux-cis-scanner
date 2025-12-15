package controls

import (
	"context"
	"fmt"
	"os"
	"os/exec"
	"strings"
	"time"
)

func CheckKernelModule(moduleName, expectedStatus string) CheckResult {
	ctx, _ := BuildScanContext()
	modInfo := ctx.GetModuleInfo(moduleName)
	
	if expectedStatus == "not_available" {
		if !modInfo.Loaded && (modInfo.Blacklisted || !modInfo.Exists) {
			if modInfo.Blacklisted {
				return Pass(
					"Module blacklisted and not loaded",
					fmt.Sprintf("install %s /bin/true", moduleName),
				)
			} else {
				return Pass(
					"Module not available in kernel",
					"module not found",
				)
			}
		} else if modInfo.Loaded {
			return Fail(
				"Module is loaded",
				fmt.Sprintf("%s loaded", moduleName),
				fmt.Sprintf("Module %s must be disabled", moduleName),
			)
		} else if modInfo.Exists && !modInfo.Blacklisted {
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
		if mountInfo, exists := ctx.Mounts[mountPoint]; exists {
			return Pass(
				fmt.Sprintf("Separate partition: %s (%s)", mountInfo.Device, mountInfo.FS),
				fmt.Sprintf("%s %s", mountInfo.Device, mountPoint),
			)
		} else {
			return Fail(
				"Not a separate partition",
				"mount not found",
				fmt.Sprintf("Mount point %s not found", mountPoint),
			)
		}
	}
	
	return Error(fmt.Errorf("unknown expected_status: %s", expectedStatus), "validation")
}

func CheckMountOption(mountPoint, requiredOption string) CheckResult {
	ctx, _ := BuildScanContext()
	
	mountInfo, runtimeExists := ctx.Mounts[mountPoint]
	if !runtimeExists {
		// CIS semantics: if partition doesn't exist, it's NOT_APPLICABLE
		return NotApplicable(
			fmt.Sprintf("Mount point %s not configured as separate partition", mountPoint),
			"mount not found",
		)
	}
	
	fstabEntry, fstabExists := ctx.Fstab[mountPoint]
	
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
	unitPaths := []string{
		fmt.Sprintf("/etc/systemd/system/%s.service", serviceName),
		fmt.Sprintf("/lib/systemd/system/%s.service", serviceName),
		fmt.Sprintf("/usr/lib/systemd/system/%s.service", serviceName),
	}
	
	unitExists := false
	for _, path := range unitPaths {
		if info, err := os.Lstat(path); err == nil && info.Mode()&os.ModeSymlink == 0 {
			unitExists = true
			break
		}
	}
	
	enabled := false
	enabledPaths := []string{
		fmt.Sprintf("/etc/systemd/system/multi-user.target.wants/%s.service", serviceName),
		fmt.Sprintf("/etc/systemd/system/default.target.wants/%s.service", serviceName),
	}
	
	for _, path := range enabledPaths {
		if _, err := os.Lstat(path); err == nil {
			enabled = true
			break
		}
	}
	
	if expectedStatus == "enabled" {
		if enabled {
			return Pass(
				fmt.Sprintf("Service %s is enabled", serviceName),
				"service enabled",
			)
		} else {
			return Fail(
				fmt.Sprintf("Service %s is not enabled", serviceName),
				"service not enabled",
				fmt.Sprintf("Service %s not enabled", serviceName),
			)
		}
	} else if expectedStatus == "disabled" || expectedStatus == "inactive" {
		if !unitExists || !enabled {
			return Pass(
				fmt.Sprintf("Service %s is disabled/not installed", serviceName),
				"service disabled",
			)
		} else {
			return Fail(
				fmt.Sprintf("Service %s is enabled", serviceName),
				"service enabled",
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