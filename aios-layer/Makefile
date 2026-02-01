SHELL := /usr/bin/env bash

.PHONY: build test bench run

build:
	go build -o bin/aios-agent ./agent
	go build -o bin/aiosctl ./cli

test:
	go test -count=2 ./agent/... ./cli/...

bench:
	mkdir -p reports
	go test ./agent/... -run ^$ -bench . -benchmem -count=2 | tee reports/bench.log

run:
	./bin/aios-agent -config config/aios.yaml
