package controls

import (
	"bufio"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"time"
)

// ScanContext - immutable system state snapshot
type ScanContext struct {
	Meta     MetaContext
	Files    FileContext
	SSH      SSHContext
	PAM      PAMContext
	Sudo     SudoContext
	Sysctl   SysctlContext
	Mounts   MountContext
	Services ServiceContext
	Packages PackageContext
	Kernel   KernelContext
	Cron     CronContext
}

// MetaContext - system metadata
type MetaContext struct {
	Hostname    string
	OSName      string
	OSVersion   string
	Kernel      string
	Arch        string
	ScanTime    time.Time
	IsContainer bool
}

// FileContext - secure file access layer
type FileContext struct {
	Stats map[string]FileStat
}

type FileStat struct {
	Exists    bool
	IsRegular bool
	IsSymlink bool
	Mode      os.FileMode
	UID       uint32
	GID       uint32
}

// SSHContext - parsed SSH configuration
type SSHContext struct {
	Config      map[string]string
	SourceFiles []string
}

// PAMContext - structured PAM configuration
type PAMContext struct {
	Files map[string][]PAMEntry
}

// SudoContext - sudo defaults
type SudoContext struct {
	Defaults []SudoDefault
}

type SudoDefault struct {
	Key     string
	Value   string
	Negated bool
	Scope   string // global only
	Source  string
}

// SysctlContext - runtime + persistent sysctl
type SysctlContext struct {
	Runtime     map[string]string
	Persistent  map[string]string
	IPv6Enabled bool
}

// MountContext - runtime + fstab mounts
type MountContext struct {
	Runtime map[string]MountInfo
	Fstab   map[string]MountInfo
}

type MountInfo struct {
	Device  string
	Options map[string]bool
	FS      string
}

// ServiceContext - systemd service states
type ServiceContext struct {
	Units map[string]ServiceState
}

type ServiceState struct {
	Installed bool
	Enabled   bool
	Active    bool
	Masked    bool
}

// PackageContext - installed packages
type PackageContext struct {
	Installed map[string]bool
}

// KernelContext - kernel modules
type KernelContext struct {
	LoadedModules map[string]bool
	Blacklisted   map[string]bool
	Available     map[string]bool
}

// KernelModuleInfo - module status
type KernelModuleInfo struct {
	Loaded      bool
	Blacklisted bool
	Exists      bool
}

// GetModuleInfo - query kernel module status
func (ctx *ScanContext) GetModuleInfo(module string) KernelModuleInfo {
	return KernelModuleInfo{
		Loaded:      ctx.Kernel.LoadedModules[module],
		Blacklisted: ctx.Kernel.Blacklisted[module],
		Exists:      ctx.Kernel.Available[module],
	}
}

// CronContext - cron file permissions
type CronContext struct {
	Files map[string]FileStat
}

// BuildScanContext - main entry point
func BuildScanContext() (*ScanContext, error) {
	ctx := &ScanContext{}

	ctx.Meta = buildMeta()
	ctx.Files = buildFileContext()
	ctx.Sysctl = buildSysctlContext()
	ctx.Mounts = buildMountContext()
	ctx.Kernel = buildKernelContext()
	ctx.Services = buildServiceContext()
	ctx.Packages = buildPackageContext()
	ctx.SSH = buildSSHContext()
	ctx.PAM = buildPAMContext()
	ctx.Sudo = buildSudoContext()
	ctx.Cron = buildCronContext()
	
	return ctx, nil
}

// buildMeta - system metadata
func buildMeta() MetaContext {
	meta := MetaContext{
		ScanTime: time.Now(),
	}
	
	if hostname, err := os.Hostname(); err == nil {
		meta.Hostname = hostname
	}
	
	if data, err := os.ReadFile("/etc/os-release"); err == nil {
		lines := strings.Split(string(data), "\n")
		for _, line := range lines {
			if strings.HasPrefix(line, "NAME=") {
				meta.OSName = strings.Trim(strings.TrimPrefix(line, "NAME="), "\"")
			}
			if strings.HasPrefix(line, "VERSION=") {
				meta.OSVersion = strings.Trim(strings.TrimPrefix(line, "VERSION="), "\"")
			}
		}
	}
	
	return meta
}

// buildFileContext - secure file stat cache
func buildFileContext() FileContext {
	files := FileContext{
		Stats: make(map[string]FileStat),
	}
	
	// Pre-populate critical files
	criticalFiles := []string{
		"/etc/ssh/sshd_config",
		"/etc/sysctl.conf",
		"/etc/fstab",
		"/etc/sudoers",
	}
	
	for _, path := range criticalFiles {
		files.Stats[path] = getFileStat(path)
	}
	
	return files
}

// getFileStat - safe file stat with symlink detection
func getFileStat(path string) FileStat {
	info, err := os.Lstat(path)
	if err != nil {
		return FileStat{Exists: false}
	}
	
	stat := FileStat{
		Exists:    true,
		IsRegular: info.Mode().IsRegular(),
		IsSymlink: info.Mode()&os.ModeSymlink != 0,
		Mode:      info.Mode(),
	}
	
	return stat
}

// buildSysctlContext - runtime + persistent sysctl (CIS compliant)
func buildSysctlContext() SysctlContext {
	ctx := SysctlContext{
		Runtime:    make(map[string]string),
		Persistent: make(map[string]string),
	}
	
	// Load runtime values from /proc/sys
	filepath.Walk("/proc/sys", func(path string, info os.FileInfo, err error) error {
		if err != nil || info.IsDir() {
			return nil
		}
		
		// Convert path to sysctl parameter name
		param := strings.TrimPrefix(path, "/proc/sys/")
		param = strings.ReplaceAll(param, "/", ".")
		
		if data, err := os.ReadFile(path); err == nil {
			ctx.Runtime[param] = strings.TrimSpace(string(data))
		}
		return nil
	})
	
	// Load persistent values from config files
	configFiles := []string{"/etc/sysctl.conf"}
	
	// Add /etc/sysctl.d/*.conf files in order
	if entries, err := os.ReadDir("/etc/sysctl.d"); err == nil {
		for _, entry := range entries {
			if strings.HasSuffix(entry.Name(), ".conf") {
				configFiles = append(configFiles, filepath.Join("/etc/sysctl.d", entry.Name()))
			}
		}
	}
	
	// Parse config files (last value wins)
	for _, file := range configFiles {
		parseSysctlFile(file, ctx.Persistent)
	}
	
	// Check IPv6 status
	if val, exists := ctx.Runtime["net.ipv6.conf.all.disable_ipv6"]; exists && val == "1" {
		ctx.IPv6Enabled = false
	} else {
		ctx.IPv6Enabled = true
	}
	
	return ctx
}

// parseSysctlFile - parse sysctl config file
func parseSysctlFile(filename string, config map[string]string) {
	// Security: reject symlinks
	if info, err := os.Lstat(filename); err != nil || info.Mode()&os.ModeSymlink != 0 {
		return
	}
	
	file, err := os.Open(filename)
	if err != nil {
		return
	}
	defer file.Close()
	
	scanner := bufio.NewScanner(file)
	for scanner.Scan() {
		line := strings.TrimSpace(scanner.Text())
		if line == "" || strings.HasPrefix(line, "#") {
			continue
		}
		
		parts := strings.SplitN(line, "=", 2)
		if len(parts) == 2 {
			key := strings.TrimSpace(parts[0])
			value := strings.TrimSpace(parts[1])
			config[key] = value
		}
	}
}

// Query methods for SysctlContext
func (s *SysctlContext) GetRuntimeValue(param string) (string, bool) {
	// IPv6 disabled logic
	if !s.IPv6Enabled && strings.Contains(param, "ipv6") {
		return "N/A", false
	}
	
	val, exists := s.Runtime[param]
	return val, exists
}

func (s *SysctlContext) IsPersistent(param, expectedValue string) bool {
	configValue, exists := s.Persistent[param]
	return exists && configValue == expectedValue
}

func (s *SysctlContext) IsIPv6Applicable(param string) bool {
	return s.IPv6Enabled || !strings.Contains(param, "ipv6")
}

// buildMountContext - parse runtime mounts and fstab
func buildMountContext() MountContext {
	ctx := MountContext{
		Runtime: make(map[string]MountInfo),
		Fstab:   make(map[string]MountInfo),
	}
	
	// Parse /proc/mounts for runtime mounts
	if file, err := os.Open("/proc/mounts"); err == nil {
		scanner := bufio.NewScanner(file)
		for scanner.Scan() {
			fields := strings.Fields(scanner.Text())
			if len(fields) >= 4 {
				device := fields[0]
				mountPoint := fields[1]
				fsType := fields[2]
				options := parseMountOptions(fields[3])
				
				ctx.Runtime[mountPoint] = MountInfo{
					Device:  device,
					Options: options,
					FS:      fsType,
				}
			}
		}
		file.Close()
	}
	
	// Parse /etc/fstab for persistent mounts
	if info, err := os.Lstat("/etc/fstab"); err == nil && info.Mode()&os.ModeSymlink == 0 {
		if file, err := os.Open("/etc/fstab"); err == nil {
			scanner := bufio.NewScanner(file)
			for scanner.Scan() {
				line := strings.TrimSpace(scanner.Text())
				if line == "" || strings.HasPrefix(line, "#") {
					continue
				}
				
				fields := strings.Fields(line)
				if len(fields) >= 3 {
					device := fields[0]
					mountPoint := fields[1]
					fsType := fields[2]
					optionsStr := ""
					if len(fields) >= 4 {
						optionsStr = fields[3]
					}
					options := parseMountOptions(optionsStr)
					
					ctx.Fstab[mountPoint] = MountInfo{
						Device:  device,
						Options: options,
						FS:      fsType,
					}
				}
			}
			file.Close()
		}
	}
	
	return ctx
}

// parseMountOptions - parse mount options string into map
func parseMountOptions(optionsStr string) map[string]bool {
	options := make(map[string]bool)
	if optionsStr == "" {
		return options
	}
	
	// Split by comma and handle key=value pairs
	parts := strings.Split(optionsStr, ",")
	for _, part := range parts {
		part = strings.TrimSpace(part)
		if part == "" {
			continue
		}
		
		// Handle key=value pairs (store just the key)
		if idx := strings.Index(part, "="); idx > 0 {
			key := part[:idx]
			options[key] = true
		} else {
			options[part] = true
		}
	}
	
	return options
}

// buildKernelContext - load kernel module information
func buildKernelContext() KernelContext {
	ctx := KernelContext{
		LoadedModules: make(map[string]bool),
		Blacklisted:   make(map[string]bool),
		Available:     make(map[string]bool),
	}
	
	// Parse /proc/modules for loaded modules
	if file, err := os.Open("/proc/modules"); err == nil {
		scanner := bufio.NewScanner(file)
		for scanner.Scan() {
			fields := strings.Fields(scanner.Text())
			if len(fields) > 0 {
				moduleName := fields[0]
				ctx.LoadedModules[moduleName] = true
				ctx.Available[moduleName] = true
			}
		}
		file.Close()
	}
	
	// Parse /etc/modprobe.d/*.conf for blacklisted modules
	modprobeDirs := []string{"/etc/modprobe.d", "/usr/lib/modprobe.d", "/run/modprobe.d"}
	for _, dir := range modprobeDirs {
		if entries, err := os.ReadDir(dir); err == nil {
			for _, entry := range entries {
				if strings.HasSuffix(entry.Name(), ".conf") {
					path := filepath.Join(dir, entry.Name())
					if info, err := os.Lstat(path); err == nil && info.Mode()&os.ModeSymlink == 0 {
						parseModprobeFile(path, &ctx)
					}
				}
			}
		}
	}
	
	// Check /proc/modules for available modules (already done above)
	// Also check /lib/modules for module files
	if uname, err := exec.Command("uname", "-r").Output(); err == nil {
		kernelVersion := strings.TrimSpace(string(uname))
		modulesDir := filepath.Join("/lib/modules", kernelVersion)
		if entries, err := os.ReadDir(modulesDir); err == nil {
			for _, entry := range entries {
				if !entry.IsDir() {
					// Module file found
					moduleName := strings.TrimSuffix(entry.Name(), ".ko")
					moduleName = strings.TrimSuffix(moduleName, ".ko.xz")
					moduleName = strings.TrimSuffix(moduleName, ".ko.zst")
					ctx.Available[moduleName] = true
				}
			}
		}
	}
	
	return ctx
}

// parseModprobeFile - parse modprobe config file for blacklist entries
func parseModprobeFile(filename string, ctx *KernelContext) {
	file, err := os.Open(filename)
	if err != nil {
		return
	}
	defer file.Close()
	
	scanner := bufio.NewScanner(file)
	for scanner.Scan() {
		line := strings.TrimSpace(scanner.Text())
		if line == "" || strings.HasPrefix(line, "#") {
			continue
		}
		
		fields := strings.Fields(line)
		if len(fields) >= 2 && (fields[0] == "blacklist" || fields[0] == "install") {
			moduleName := fields[1]
			ctx.Blacklisted[moduleName] = true
			
			// For "install module /bin/true" or "install module /bin/false"
			if fields[0] == "install" && len(fields) >= 3 {
				if strings.Contains(fields[2], "/bin/true") || strings.Contains(fields[2], "/bin/false") {
					ctx.Blacklisted[moduleName] = true
				}
			}
		}
	}
}

// buildServiceContext - query systemd for service states
func buildServiceContext() ServiceContext {
	ctx := ServiceContext{
		Units: make(map[string]ServiceState),
	}
	
	// Use systemctl to get all unit files
	cmd := exec.Command("systemctl", "list-unit-files", "--type=service", "--no-pager", "--no-legend")
	if output, err := cmd.Output(); err == nil {
		lines := strings.Split(string(output), "\n")
		for _, line := range lines {
			fields := strings.Fields(line)
			if len(fields) >= 2 {
				unitName := fields[0]
				// Remove .service suffix if present
				unitName = strings.TrimSuffix(unitName, ".service")
				state := fields[1]
				
				stateObj := ServiceState{
					Installed: true,
					Enabled:   state == "enabled" || state == "enabled-runtime",
					Masked:    state == "masked" || state == "masked-runtime",
				}
				
				// Check if service is active
				activeCmd := exec.Command("systemctl", "is-active", "--quiet", unitName+".service")
				stateObj.Active = activeCmd.Run() == nil
				
				ctx.Units[unitName] = stateObj
			}
		}
	}
	
	return ctx
}

// buildPackageContext - cache installed packages
func buildPackageContext() PackageContext {
	ctx := PackageContext{
		Installed: make(map[string]bool),
	}
	
	// Query all installed packages
	cmd := exec.Command("rpm", "-qa", "--queryformat", "%{NAME}\n")
	if output, err := cmd.Output(); err == nil {
		lines := strings.Split(string(output), "\n")
		for _, line := range lines {
			pkgName := strings.TrimSpace(line)
			if pkgName != "" {
				ctx.Installed[pkgName] = true
			}
		}
	}
	
	return ctx
}

// buildSSHContext - parse SSH configuration
func buildSSHContext() SSHContext {
	ctx := SSHContext{
		Config:      make(map[string]string),
		SourceFiles: []string{},
	}
	
	// Use existing SSH parsing logic from ssh.go
	// For now, we'll parse it here to avoid circular dependencies
	sshConfigPath := "/etc/ssh/sshd_config"
	if info, err := os.Lstat(sshConfigPath); err == nil && info.Mode()&os.ModeSymlink == 0 {
		parseSSHConfigForContext(sshConfigPath, &ctx)
	}
	
	return ctx
}

// parseSSHConfigForContext - parse SSH config into context (simplified version)
func parseSSHConfigForContext(path string, ctx *SSHContext) {
	file, err := os.Open(path)
	if err != nil {
		return
	}
	defer file.Close()
	
	ctx.SourceFiles = append(ctx.SourceFiles, path)
	scanner := bufio.NewScanner(file)
	
	for scanner.Scan() {
		line := strings.TrimSpace(scanner.Text())
		if line == "" || strings.HasPrefix(line, "#") {
			continue
		}
		
		// Strip inline comments
		if idx := strings.Index(line, "#"); idx != -1 {
			line = strings.TrimSpace(line[:idx])
		}
		
		fields := strings.Fields(line)
		if len(fields) >= 2 {
			key := strings.ToLower(fields[0])
			value := strings.Join(fields[1:], " ")
			ctx.Config[key] = value
		}
	}
}

// buildPAMContext - parse PAM configuration files
func buildPAMContext() PAMContext {
	ctx := PAMContext{
		Files: make(map[string][]PAMEntry),
	}
	
	// Parse common PAM files
	pamFiles := []string{
		"/etc/pam.d/system-auth",
		"/etc/pam.d/password-auth",
		"/etc/pam.d/login",
		"/etc/pam.d/sshd",
		"/etc/pam.d/sudo",
	}
	
	for _, pamFile := range pamFiles {
		if entries, err := parsePAMFileForContext(pamFile); err == nil {
			ctx.Files[pamFile] = entries
		}
	}
	
	return ctx
}

// parsePAMFileForContext - parse PAM file (simplified version for context)
func parsePAMFileForContext(path string) ([]PAMEntry, error) {
	info, err := os.Lstat(path)
	if err != nil {
		return nil, err
	}
	if info.Mode()&os.ModeSymlink != 0 {
		return nil, nil // Skip symlinks
	}
	
	file, err := os.Open(path)
	if err != nil {
		return nil, err
	}
	defer file.Close()
	
	var entries []PAMEntry
	scanner := bufio.NewScanner(file)
	
	for scanner.Scan() {
		line := strings.TrimSpace(scanner.Text())
		if line == "" || strings.HasPrefix(line, "#") {
			continue
		}
		
		fields := strings.Fields(line)
		if len(fields) >= 3 {
			entry := PAMEntry{
				Type:      fields[0],
				Control:   fields[1],
				Module:    filepath.Base(fields[2]),
				Arguments: make(map[string]string),
				RawLine:   line,
			}
			
			// Parse arguments
			for _, arg := range fields[3:] {
				if strings.Contains(arg, "=") {
					kv := strings.SplitN(arg, "=", 2)
					if len(kv) == 2 {
						entry.Arguments[kv[0]] = strings.Trim(kv[1], `"`)
					}
				}
			}
			
			entries = append(entries, entry)
		}
	}
	
	return entries, nil
}

// buildSudoContext - parse sudoers configuration
func buildSudoContext() SudoContext {
	ctx := SudoContext{
		Defaults: []SudoDefault{},
	}
	
	sudoersPath := "/etc/sudoers"
	if info, err := os.Lstat(sudoersPath); err == nil && info.Mode()&os.ModeSymlink == 0 {
		parseSudoersForContext(sudoersPath, &ctx)
	}
	
	return ctx
}

// parseSudoersForContext - parse sudoers file for Defaults
func parseSudoersForContext(path string, ctx *SudoContext) {
	file, err := os.Open(path)
	if err != nil {
		return
	}
	defer file.Close()
	
	scanner := bufio.NewScanner(file)
	for scanner.Scan() {
		line := strings.TrimSpace(scanner.Text())
		if line == "" || strings.HasPrefix(line, "#") {
			continue
		}
		
		// Only process Defaults lines (global only, no colon or @)
		if !strings.HasPrefix(line, "Defaults") {
			continue
		}
		
		fields := strings.Fields(line)
		if len(fields) < 2 {
			continue
		}
		
		// Skip scoped defaults
		if strings.Contains(fields[0], ":") || strings.Contains(fields[0], "@") {
			continue
		}
		
		// Parse each default setting
		for _, field := range fields[1:] {
			d := SudoDefault{Source: path}
			
			// Handle negation
			if strings.HasPrefix(field, "!") {
				d.Negated = true
				field = strings.TrimPrefix(field, "!")
			}
			
			// Handle key=value pairs
			if strings.Contains(field, "=") {
				kv := strings.SplitN(field, "=", 2)
				if len(kv) == 2 {
					d.Key = kv[0]
					d.Value = strings.Trim(kv[1], `"`)
				}
			} else {
				// Handle flags
				d.Key = field
				d.Value = "enabled"
			}
			
			ctx.Defaults = append(ctx.Defaults, d)
		}
	}
}

// buildCronContext - check cron file permissions
func buildCronContext() CronContext {
	ctx := CronContext{
		Files: make(map[string]FileStat),
	}
	
	// Check common cron files
	cronFiles := []string{
		"/etc/crontab",
		"/etc/cron.hourly",
		"/etc/cron.daily",
		"/etc/cron.weekly",
		"/etc/cron.monthly",
		"/etc/cron.d",
		"/var/spool/cron/root",
		"/var/spool/cron/crontabs/root",
	}
	
	for _, cronFile := range cronFiles {
		ctx.Files[cronFile] = getFileStat(cronFile)
	}
	
	return ctx
}
