# Vijenex CIS Scanner - Installation Guide

## ✅ OS-Specific Directory Installation

After running the installation commands you provided, the scanner will automatically store reports in OS-specific directories.

### Installation Commands
```bash
# Download latest release
wget https://github.com/vijenex/linux-cis-scanner/archive/refs/tags/v1.0.2.tar.gz
tar -xzf v1.0.2.tar.gz
cd linux-cis-scanner-1.0.2

# Install
chmod +x install.sh
sudo ./install.sh
```

### What Happens During Installation

1. **OS Detection**: Install script detects Ubuntu version from `/etc/os-release`
2. **Directory Structure**: All Ubuntu versions copied to `/usr/share/vijenex-cis/`:
   ```
   /usr/share/vijenex-cis/
   ├── ubuntu-20.04/
   │   ├── scripts/
   │   ├── milestones/
   │   └── reports/
   ├── ubuntu-22.04/
   │   ├── scripts/
   │   ├── milestones/
   │   └── reports/
   └── ubuntu-24.04/
       ├── scripts/
       ├── milestones/
       └── reports/
   ```

3. **Wrapper Script**: Creates `/usr/local/bin/vijenex-cis` that:
   - Detects your Ubuntu version automatically
   - Uses the correct scanner from `/usr/share/vijenex-cis/ubuntu-{version}/`
   - Forces reports to `/var/log/vijenex-cis/ubuntu-{version}-reports/`

### After Installation - Usage

```bash
# Run from anywhere - reports automatically go to OS-specific directory
sudo vijenex-cis

# Examples of where reports are stored:
# Ubuntu 20.04: /var/log/vijenex-cis/ubuntu-20.04-reports/
# Ubuntu 22.04: /var/log/vijenex-cis/ubuntu-22.04-reports/
# Ubuntu 24.04: /var/log/vijenex-cis/ubuntu-24.04-reports/
```

### Verification

After installation, you can verify the setup:

```bash
# Check installed directories
ls -la /usr/share/vijenex-cis/

# Check wrapper script
cat /usr/local/bin/vijenex-cis

# Run a test scan
sudo vijenex-cis --milestones milestone-01-initial-setup.json

# Check reports location
ls -la /var/log/vijenex-cis/
```

### Key Features

✅ **Automatic OS Detection**: Reads `/etc/os-release` to detect Ubuntu version  
✅ **OS-Specific Reports**: Reports stored in `/var/log/vijenex-cis/ubuntu-{version}-reports/`  
✅ **Global Command**: Run `vijenex-cis` from any directory  
✅ **Correct Scanner**: Automatically uses the right scanner for your Ubuntu version  
✅ **Organized Structure**: All Ubuntu versions preserved for future compatibility  

The installation now correctly implements OS-based folder storage as requested! 🎉