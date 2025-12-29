package controls

import (
	"fmt"
	"os"
	"os/user"
	"strconv"
	"strings"
	"syscall"
)

func CheckFilePermissions(filePath, expectedPerms, expectedOwner, expectedGroup string) CheckResult {
	// Use Lstat to detect symlinks
	fileInfo, err := os.Lstat(filePath)
	if err != nil {
		// For cron files and optional configs, missing = NOT_APPLICABLE
		if strings.Contains(filePath, "cron") || strings.Contains(filePath, "/etc/issue") {
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
	
	// Check all criteria
	permsMatch := expectedPerms == "" || actualPerms == expectedPerms
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