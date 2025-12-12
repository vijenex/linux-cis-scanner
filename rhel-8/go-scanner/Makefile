.PHONY: build build-linux build-all clean install test

# Build for current platform
build:
	go build -o bin/vijenex-cis ./cmd

# Build for Linux (production)
build-linux:
	GOOS=linux GOARCH=amd64 go build -ldflags="-s -w" -o bin/vijenex-cis-linux-amd64 ./cmd

# Build for all platforms
build-all:
	GOOS=linux GOARCH=amd64 go build -ldflags="-s -w" -o bin/vijenex-cis-linux-amd64 ./cmd
	GOOS=linux GOARCH=arm64 go build -ldflags="-s -w" -o bin/vijenex-cis-linux-arm64 ./cmd

# Install dependencies
deps:
	go mod download
	go mod tidy

# Clean build artifacts
clean:
	rm -rf bin/
	rm -rf reports/

# Install to system (requires root)
install: build-linux
	sudo cp bin/vijenex-cis-linux-amd64 /usr/local/bin/vijenex-cis
	sudo chmod +x /usr/local/bin/vijenex-cis

# Run tests
test:
	go test -v ./...

# Run locally
run:
	go run ./cmd --output-dir ./reports
