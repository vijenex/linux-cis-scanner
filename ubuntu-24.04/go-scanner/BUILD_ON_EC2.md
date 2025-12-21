# 🔨 Building Scanner on EC2 (No File Transfer Needed)

Since you can't copy files from Mac to EC2, build directly on the EC2 instance.

## Quick Setup (One-Time)

```bash
# On your EC2 instance:
cd ~/linux-cis-scanner/ubuntu-24.04/go-scanner

# Install Go (one-time setup)
./install-go.sh

# Add Go to PATH for current session
export PATH=$PATH:$HOME/go/go/bin
export GOPATH=$HOME/go

# Verify Go installation
go version

# Build the scanner
./build.sh

# Run the scanner
sudo ./bin/vijenex-cis-amd64
```

## Permanent Setup (Add to ~/.bashrc)

```bash
# Add to ~/.bashrc so Go is available in all sessions
echo 'export PATH=$PATH:$HOME/go/go/bin' >> ~/.bashrc
echo 'export GOPATH=$HOME/go' >> ~/.bashrc

# Reload
source ~/.bashrc

# Now you can build anytime
cd ~/linux-cis-scanner/ubuntu-24.04/go-scanner
./build.sh
```

## Alternative: Use Wrapper Script

The `vijenex-cis` wrapper will automatically build if Go is installed:

```bash
cd ~/linux-cis-scanner/ubuntu-24.04/go-scanner

# Install Go first (one-time)
./install-go.sh
export PATH=$PATH:$HOME/go/go/bin

# Run wrapper - it will auto-build
sudo ./vijenex-cis
```

## What Gets Installed

- Go 1.21.5 (latest stable)
- Installed to: `~/go/go/`
- No root required
- ~150MB download

## After Building

The binary will be in:
- `bin/vijenex-cis-amd64` (for x86_64)
- `bin/vijenex-cis-arm64` (for ARM64)

You can then run:
```bash
sudo ./bin/vijenex-cis-amd64
```

## Troubleshooting

If `install-go.sh` fails:
```bash
# Manual installation
cd ~
wget https://go.dev/dl/go1.21.5.linux-amd64.tar.gz
tar -xzf go1.21.5.linux-amd64.tar.gz
export PATH=$PATH:~/go/bin
go version
```

