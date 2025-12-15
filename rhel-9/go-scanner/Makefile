.PHONY: build clean install

BINARY_NAME=vijenex-cis
BUILD_DIR=bin

build:
	@echo "Building RHEL 9 CIS Scanner..."
	go build -o $(BUILD_DIR)/$(BINARY_NAME) cmd/main.go
	@echo "Build complete: $(BUILD_DIR)/$(BINARY_NAME)"

clean:
	@echo "Cleaning..."
	rm -rf $(BUILD_DIR)
	rm -rf reports

install: build
	@echo "Installing to /usr/local/bin..."
	sudo cp $(BUILD_DIR)/$(BINARY_NAME) /usr/local/bin/
	@echo "Installation complete"

test:
	go test ./...
