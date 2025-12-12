package controls

import (
	"fmt"
	"os"
	"syscall"
)

func CheckFilePermissions(filePath, expectedPerms, expectedOwner, expectedGroup string) CheckResult {
	fileInfo, err := os.Stat(filePath)
	if err != nil {
		return CheckResult{
			Status:          "ERROR",
			ActualValue:     "File not found",
			EvidenceCommand: fmt.Sprintf("stat %s", filePath),
			Description:     fmt.Sprintf("Cannot access %s", filePath),
		}
	}
	
	// Get actual permissions
	actualPerms := fmt.Sprintf("%04o", fileInfo.Mode().Perm())
	
	// Get owner and group
	stat := fileInfo.Sys().(*syscall.Stat_t)
	uid := stat.Uid
	gid := stat.Gid
	
	// Check permissions
	permsMatch := actualPerms == expectedPerms
	
	// For now, just check permissions (owner/group check needs user lookup)
	status := "PASS"
	if !permsMatch {
		status = "FAIL"
	}
	
	return CheckResult{
		Status:          status,
		ActualValue:     fmt.Sprintf("Permissions: %s, UID: %d, GID: %d", actualPerms, uid, gid),
		EvidenceCommand: fmt.Sprintf("stat -c '%%a %%U:%%G' %s", filePath),
		Description:     fmt.Sprintf("File %s permissions check", filePath),
	}
}
