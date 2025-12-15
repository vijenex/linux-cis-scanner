package controls

import (
	"bufio"
	"os"
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
	// TODO: Add other builders incrementally
	
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
