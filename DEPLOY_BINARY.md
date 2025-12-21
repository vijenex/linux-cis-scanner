# 📦 Deploy Binary to Remote Server

## Option 1: Copy Pre-built Binary (Recommended)

The binary has been built locally. Copy it to your remote server:

```bash
# From your local machine (Mac):
cd ~/Desktop/Vijenex/linux-cis-scanner/ubuntu-24.04/go-scanner

# Copy binary to remote server
scp bin/vijenex-cis-amd64 root@ip-172-18-0-143:~/linux-cis-scanner/ubuntu-24.04/go-scanner/bin/

# OR copy to the go-scanner directory directly
scp bin/vijenex-cis-amd64 root@ip-172-18-0-143:~/linux-cis-scanner/ubuntu-24.04/go-scanner/

# On remote server, make it executable:
ssh root@ip-172-18-0-143
cd ~/linux-cis-scanner/ubuntu-24.04/go-scanner
chmod +x bin/vijenex-cis-amd64
# OR if copied to go-scanner directory:
chmod +x vijenex-cis-amd64

# Run it:
sudo ./bin/vijenex-cis-amd64
# OR:
sudo ./vijenex-cis-amd64
```

## Option 2: Install Go on Remote Server

If you prefer to build on the remote server:

```bash
# On remote server:
cd /tmp
wget https://go.dev/dl/go1.21.5.linux-amd64.tar.gz
sudo rm -rf /usr/local/go
sudo tar -C /usr/local -xzf go1.21.5.linux-amd64.tar.gz
export PATH=$PATH:/usr/local/go/bin
echo 'export PATH=$PATH:/usr/local/go/bin' >> ~/.bashrc

# Verify Go installation:
go version

# Now build:
cd ~/linux-cis-scanner/ubuntu-24.04/go-scanner
./build.sh
```

## Option 3: Use the Wrapper Script

The wrapper script should automatically use the binary if it's in the right place:

```bash
# On remote server:
cd ~/linux-cis-scanner/ubuntu-24.04/go-scanner

# Make sure binary is in bin/ directory:
mkdir -p bin
# (Copy binary here using Option 1)

# Run wrapper:
sudo ./vijenex-cis
```

## Verification

After copying/building, verify the binary:

```bash
# Check if binary contains debug code:
strings bin/vijenex-cis-amd64 | grep "\[DEBUG\]"

# Should output: [DEBUG]
# If no output, the binary is old
```

## Expected Results

After running with the new binary:
- You should see debug output: `[DEBUG] 1.1.1.1: type=...`
- Manual count: ~6 (down from 148)
- Automated count: ~195 (up from ~53)

