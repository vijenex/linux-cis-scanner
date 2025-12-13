# Vijenex CIS Scanner - Go Binary Deployment

## Why Go-Only?

✅ **No Dependencies** - Single 4.4MB binary, no Python needed
✅ **Easy Deployment** - Copy to 50 machines and run
✅ **Like OpenSCAP** - Compiled binary approach
✅ **Faster** - Native compiled code
✅ **Simpler** - No version conflicts or missing packages

## Deployment Steps

### 1. Copy Binary to RHEL 8 Servers

```bash
# From your Mac/local machine
scp rhel-8/vijenex-cis-amd64 root@rhel-server:/usr/local/bin/vijenex-cis
```

### 2. Run Scanner on Each Server

```bash
# SSH to RHEL server
ssh root@rhel-server

# Run Level 1 scan
/usr/local/bin/vijenex-cis --profile Level1 --output-dir /tmp/scan-results

# Or run Level 2 scan
/usr/local/bin/vijenex-cis --profile Level2 --output-dir /tmp/scan-results
```

### 3. Collect Reports

```bash
# Copy HTML report back to your machine
scp root@rhel-server:/tmp/scan-results/vijenex-cis-report.html ./reports/server1-report.html

# Copy CSV for consolidation
scp root@rhel-server:/tmp/scan-results/vijenex-cis-results.csv ./reports/server1-results.csv
```

## Automated Deployment Script

```bash
#!/bin/bash
# deploy-scanner.sh

SERVERS=(
  "server1.example.com"
  "server2.example.com"
  "server3.example.com"
  # ... add all 50 servers
)

BINARY="rhel-8/vijenex-cis-amd64"

for server in "${SERVERS[@]}"; do
  echo "Deploying to $server..."
  scp $BINARY root@$server:/usr/local/bin/vijenex-cis
  ssh root@$server "chmod +x /usr/local/bin/vijenex-cis"
done

echo "✅ Deployed to ${#SERVERS[@]} servers"
```

## Automated Scanning Script

```bash
#!/bin/bash
# scan-all-servers.sh

SERVERS=(
  "server1.example.com"
  "server2.example.com"
  # ... add all 50 servers
)

mkdir -p reports

for server in "${SERVERS[@]}"; do
  echo "Scanning $server..."
  
  # Run scan
  ssh root@$server "/usr/local/bin/vijenex-cis --profile Level1 --output-dir /tmp/scan-results"
  
  # Collect reports
  scp root@$server:/tmp/scan-results/vijenex-cis-report.html reports/${server}-report.html
  scp root@$server:/tmp/scan-results/vijenex-cis-results.csv reports/${server}-results.csv
  
  echo "✅ Completed $server"
done

echo "✅ All scans complete! Reports in ./reports/"
```

## Scanner Features

### Controls
- **Total**: 447 controls
- **Automated**: 266 controls (exceeds OpenSCAP's 256!)
- **Manual**: 181 controls

### Report Formats
- **HTML**: Professional expandable report with JavaScript
- **CSV**: For consolidation and analysis

### Profiles
- **Level1**: 186 automated controls (basic hardening)
- **Level2**: 266 automated controls (all controls)

## Comparison with OpenSCAP

| Feature | OpenSCAP | Vijenex |
|---------|----------|---------|
| Binary Size | ~2MB | 4.4MB |
| Dependencies | libxml2, etc | None |
| Automated Controls | ~256 | 266 ✅ |
| HTML Report | Basic | Professional with expandable controls |
| Deployment | Package manager | Single binary copy |
| Speed | 5-10 min | 1-2 min |

## Troubleshooting

### Permission Denied
```bash
chmod +x /usr/local/bin/vijenex-cis
```

### Must Run as Root
```bash
sudo /usr/local/bin/vijenex-cis --profile Level1 --output-dir /tmp/scan-results
```

### Check Scanner Version
```bash
/usr/local/bin/vijenex-cis --help
```

## Next Steps

1. ✅ Test on 1 RHEL 8 server
2. ✅ Verify HTML report shows 266 automated controls
3. ✅ Deploy to all 50 servers
4. ✅ Run scans and collect reports
5. ✅ Generate consolidated report
