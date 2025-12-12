# Quick Start - Building & Installing Packages

## 🚀 Build Packages (5 Minutes)

### On RHEL 8 Machine

```bash
# 1. Install build tools
sudo yum install rpm-build

# 2. Navigate to project
cd /path/to/Linux-CIS-Audit-code

# 3. Build RPM
./packaging/build-rpm.sh

# 4. Package created!
ls packaging/rpm/dist/vijenex-cis-scanner-1.0.0-1.*.rpm
```

### On Ubuntu 22.04 Machine

```bash
# 1. Install build tools
sudo apt install dpkg-dev

# 2. Navigate to project
cd /path/to/Linux-CIS-Audit-code

# 3. Build DEB
./packaging/build-deb.sh

# 4. Package created!
ls packaging/deb/dist/vijenex-cis-scanner_1.0.0_all.deb
```

## 📦 Install Package (1 Minute)

### RHEL/CentOS

```bash
# Install
sudo yum localinstall vijenex-cis-scanner-1.0.0-1.*.rpm

# Verify
which vijenex-cis
man vijenex-cis
```

### Ubuntu/Debian

```bash
# Install
sudo apt install ./vijenex-cis-scanner_1.0.0_all.deb

# Verify
which vijenex-cis
man vijenex-cis
```

## ✅ Run Scanner (30 Seconds)

```bash
# Complete scan
sudo vijenex-cis

# Level 2 scan
sudo vijenex-cis --profile Level2

# Custom output
sudo vijenex-cis --output-dir /tmp/reports

# View reports
ls /var/log/vijenex-cis/*/
```

## 🎯 That's It!

No cloning repos, no Python paths, no manual setup.

**Just install and run - like OpenSCAP!**
