.PHONY: build clean test install

build:
	@echo "Building Vijenex CIS Scanner for CentOS 7..."
	@./build.sh

clean:
	@echo "Cleaning build artifacts..."
	@rm -rf bin/vijenex-cis*
	@rm -rf reports/
	@go clean

test:
	@echo "Running tests..."
	@go test ./...

install: build
	@echo "Installing binary..."
	@cp bin/vijenex-cis-amd64 /usr/local/bin/vijenex-cis
	@chmod +x /usr/local/bin/vijenex-cis
	@echo "Installed to /usr/local/bin/vijenex-cis"

deps:
	@echo "Downloading dependencies..."
	@go mod download
	@go mod tidy
