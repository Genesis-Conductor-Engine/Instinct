.PHONY: help fmt lint test build agent cli demo

help:
	@echo "Targets: fmt lint test build agent cli demo"

fmt:
	@go fmt ./...

lint:
	@go vet ./...

test:
	@go test ./...

build: agent cli

agent:
	@go build -o bin/aios-agent ./agent

cli:
	@go build -o bin/aiosctl ./cli

demo:
	@./scripts/demo.sh
