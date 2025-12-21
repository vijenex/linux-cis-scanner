package controls

import (
	"fmt"
	"os"
	"os/user"
	"path/filepath"
	"strconv"
	"strings"
	"syscall"
)

func CheckFilePermissions(filePath, expectedPerms, expectedOwner, expectedGroup string) CheckResult {
	// Check if filePath contains glob patterns (e.g., /etc/ssh/ssh_host_*_key.pub)
	if strings.Contains(filePath, "*") {
		return checkGlobFilePermissions(filePath, expectedPerms, expectedOwner, expectedGroup)
	}
	
	// Use Lstat to detect symlinks
	fileInfo, err := os.Lstat(filePath)
	if err != nil {
		// For cron files and optional configs, missing = NOT_APPLICABLE
		// Only return NOT_APPLICABLE if file doesn't exist AND it's an optional file
		if strings.Contains(filePath, "cron") {
			return NotApplicable(
				fmt.Sprintf("Directory %s does not exist", filePath),
				"directory not found",
			)
		}
		// For /etc/issue files, only return NOT_APPLICABLE if they don't exist
		// (they're optional in some configurations)
		if strings.Contains(filePath, "/etc/issue") && !strings.Contains(filePath, "/etc/issue.net") {
			// /etc/issue is optional, but /etc/issue.net should exist if SSH is configured
			return NotApplicable(
				fmt.Sprintf("File %s does not exist", filePath),
				"file not found",
			)
		}
		return Error(err, filePath)
	}
	
	// Reject symlinks for security
	if fileInfo.Mode()&os.ModeSymlink != 0 {
		return CheckResult{
			Status:      StatusFail,
			ActualValue: "Symlink not allowed",
			Evidence:    Evidence{Method: "file", Source: filePath, Snippet: "symlink"},
			Description: fmt.Sprintf("Symlink rejected: %s", filePath),
		}
	}
	
	// Get actual permissions (including sticky bit)
	actualPerms := fmt.Sprintf("%04o", fileInfo.Mode().Perm())
	if fileInfo.Mode()&os.ModeSticky != 0 {
		// Add sticky bit to permissions
		permInt, _ := strconv.ParseInt(actualPerms, 8, 32)
		permInt |= 01000
		actualPerms = fmt.Sprintf("%04o", permInt)
	}
	
	// Get owner and group
	stat := fileInfo.Sys().(*syscall.Stat_t)
	uid := stat.Uid
	gid := stat.Gid
	
	// Lookup username and groupname
	actualOwner := fmt.Sprintf("%d", uid)
	actualGroup := fmt.Sprintf("%d", gid)
	
	if u, err := user.LookupId(fmt.Sprintf("%d", uid)); err == nil {
		actualOwner = u.Username
	}
	if g, err := user.LookupGroupId(fmt.Sprintf("%d", gid)); err == nil {
		actualGroup = g.Name
	}
	
	// Check if path is a directory - if so, check all files in it
	if fileInfo.IsDir() {
		return checkDirectoryPermissions(filePath, expectedPerms, expectedOwner, expectedGroup)
	}
	
	// Check all criteria for single file
	permsMatch := checkPermissionsMatch(actualPerms, expectedPerms)
	ownerMatch := expectedOwner == "" || actualOwner == expectedOwner
	groupMatch := expectedGroup == "" || actualGroup == expectedGroup
	
	status := StatusPass
	if !permsMatch || !ownerMatch || !groupMatch {
		status = StatusFail
	}
	
	return CheckResult{
		Status:      status,
		ActualValue: fmt.Sprintf("Permissions: %s, Owner: %s, Group: %s", actualPerms, actualOwner, actualGroup),
		Evidence:    Evidence{Method: "file", Source: filePath, Snippet: fmt.Sprintf("%s %s:%s", actualPerms, actualOwner, actualGroup)},
		Description: fmt.Sprintf("File %s permissions check", filePath),
	}
}

// checkPermissionsMatch - check if actual permissions match expected (supports "or more restrictive")
func checkPermissionsMatch(actualPerms, expectedPerms string) bool {
	if expectedPerms == "" {
		return true
	}
	
	// Exact match
	if actualPerms == expectedPerms {
		return true
	}
	
	// Check if "or more restrictive" - convert to numeric and compare
	actualInt, err1 := strconv.ParseInt(actualPerms, 8, 32)
	expectedInt, err2 := strconv.ParseInt(expectedPerms, 8, 32)
	
	if err1 != nil || err2 != nil {
		// If parsing fails, fall back to exact match
		return actualPerms == expectedPerms
	}
	
	// "More restrictive" means lower numeric value in octal
	// e.g., 600 is more restrictive than 640, 640 is more restrictive than 644
	// So actual <= expected means "actual is as restrictive or more restrictive"
	return actualInt <= expectedInt
}

// checkDirectoryPermissions - check all files in a directory
func checkDirectoryPermissions(dirPath, expectedPerms, expectedOwner, expectedGroup string) CheckResult {
	var failures []string
	var checkedFiles int
	
	err := filepath.Walk(dirPath, func(path string, info os.FileInfo, err error) error {
		if err != nil {
			return nil // Skip errors, continue checking other files
		}
		
		// Only check regular files (not directories)
		if !info.Mode().IsRegular() {
			return nil
		}
		
		// Skip symlinks
		if info.Mode()&os.ModeSymlink != 0 {
			return nil
		}
		
		checkedFiles++
		
		// Get file permissions
		actualPerms := fmt.Sprintf("%04o", info.Mode().Perm())
		
		// Get owner and group
		stat := info.Sys().(*syscall.Stat_t)
		uid := stat.Uid
		gid := stat.Gid
		
		actualOwner := fmt.Sprintf("%d", uid)
		actualGroup := fmt.Sprintf("%d", gid)
		
		if u, err := user.LookupId(fmt.Sprintf("%d", uid)); err == nil {
			actualOwner = u.Username
		}
		if g, err := user.LookupGroupId(fmt.Sprintf("%d", gid)); err == nil {
			actualGroup = g.Name
		}
		
		// Check permissions (supports "or more restrictive")
		permsMatch := checkPermissionsMatch(actualPerms, expectedPerms)
		ownerMatch := expectedOwner == "" || actualOwner == expectedOwner
		groupMatch := expectedGroup == "" || actualGroup == expectedGroup
		
		if !permsMatch || !ownerMatch || !groupMatch {
			failures = append(failures, fmt.Sprintf("%s: %s %s:%s", path, actualPerms, actualOwner, actualGroup))
		}
		
		return nil
	})
	
	if err != nil {
		return Error(err, dirPath)
	}
	
	if len(failures) == 0 {
		return CheckResult{
			Status:      StatusPass,
			ActualValue: fmt.Sprintf("All %d files have correct permissions", checkedFiles),
			Evidence:    Evidence{Method: "directory", Source: dirPath, Snippet: fmt.Sprintf("checked %d files", checkedFiles)},
			Description: fmt.Sprintf("Directory %s permissions check", dirPath),
		}
	}
	
	return CheckResult{
		Status:      StatusFail,
		ActualValue: fmt.Sprintf("%d files with incorrect permissions: %s", len(failures), strings.Join(failures[:min(3, len(failures))], "; ")),
		Evidence:    Evidence{Method: "directory", Source: dirPath, Snippet: strings.Join(failures[:min(3, len(failures))], "; ")},
		Description: fmt.Sprintf("Directory %s has files with incorrect permissions", dirPath),
	}
}

func min(a, b int) int {
	if a < b {
		return a
	}
	return b
}

// checkGlobFilePermissions - check permissions for files matching a glob pattern
func checkGlobFilePermissions(globPattern, expectedPerms, expectedOwner, expectedGroup string) CheckResult {
	// Extract directory and pattern
	dir := filepath.Dir(globPattern)
	pattern := filepath.Base(globPattern)
	
	// Find all matching files
	matches, err := filepath.Glob(globPattern)
	if err != nil {
		return Error(fmt.Errorf("glob pattern error: %v", err), globPattern)
	}
	
	if len(matches) == 0 {
		// No files match - check if directory exists
		if _, err := os.Stat(dir); os.IsNotExist(err) {
			return NotApplicable(
				fmt.Sprintf("Directory %s does not exist", dir),
				"directory not found",
			)
		}
		// Directory exists but no matching files - FAIL
		return CheckResult{
			Status:      StatusFail,
			ActualValue: fmt.Sprintf("No files matching pattern %s found", pattern),
			Evidence:    Evidence{Method: "glob", Source: globPattern, Snippet: "no matches"},
			Description: fmt.Sprintf("No files found matching %s", globPattern),
		}
	}
	
	// Check all matching files
	var failures []string
	var checkedFiles int
	
	for _, match := range matches {
		// Skip directories
		info, err := os.Lstat(match)
		if err != nil || !info.Mode().IsRegular() {
			continue
		}
		
		// Skip symlinks
		if info.Mode()&os.ModeSymlink != 0 {
			continue
		}
		
		checkedFiles++
		
		// Get file permissions
		actualPerms := fmt.Sprintf("%04o", info.Mode().Perm())
		
		// Get owner and group
		stat := info.Sys().(*syscall.Stat_t)
		uid := stat.Uid
		gid := stat.Gid
		
		actualOwner := fmt.Sprintf("%d", uid)
		actualGroup := fmt.Sprintf("%d", gid)
		
		if u, err := user.LookupId(fmt.Sprintf("%d", uid)); err == nil {
			actualOwner = u.Username
		}
		if g, err := user.LookupGroupId(fmt.Sprintf("%d", gid)); err == nil {
			actualGroup = g.Name
		}
		
		// Check permissions (supports "or more restrictive")
		permsMatch := checkPermissionsMatch(actualPerms, expectedPerms)
		ownerMatch := expectedOwner == "" || actualOwner == expectedOwner
		groupMatch := expectedGroup == "" || actualGroup == expectedGroup
		
		if !permsMatch || !ownerMatch || !groupMatch {
			failures = append(failures, fmt.Sprintf("%s: %s %s:%s", match, actualPerms, actualOwner, actualGroup))
		}
	}
	
	if len(failures) == 0 {
		return CheckResult{
			Status:      StatusPass,
			ActualValue: fmt.Sprintf("All %d files have correct permissions", checkedFiles),
			Evidence:    Evidence{Method: "glob", Source: globPattern, Snippet: fmt.Sprintf("checked %d files", checkedFiles)},
			Description: fmt.Sprintf("Glob pattern %s permissions check", globPattern),
		}
	}
	
	return CheckResult{
		Status:      StatusFail,
		ActualValue: fmt.Sprintf("%d files with incorrect permissions: %s", len(failures), strings.Join(failures[:min(3, len(failures))], "; ")),
		Evidence:    Evidence{Method: "glob", Source: globPattern, Snippet: strings.Join(failures[:min(3, len(failures))], "; ")},
		Description: fmt.Sprintf("Glob pattern %s has files with incorrect permissions", globPattern),
	}
}