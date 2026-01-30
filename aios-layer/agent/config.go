package main

import (
	"fmt"
	"os"

	"gopkg.in/yaml.v3"
)

type Config struct {
	Server  ServerConfig  `yaml:"server"`
	Policy  PolicyConfig  `yaml:"policy"`
	Runtime RuntimeConfig `yaml:"runtime"`
	GPU     GPUConfig     `yaml:"gpu"`
}

type ServerConfig struct {
	ListenAddr string `yaml:"listen_addr"`
}

type PolicyConfig struct {
	AllowedUsers     []string      `yaml:"allowed_users"`
	MaxLeaseSeconds  int           `yaml:"max_lease_seconds"`
	MaxConcurrent    int           `yaml:"max_concurrent_leases"`
	DefaultLeaseSecs int           `yaml:"default_lease_seconds"`
	GPUQuota         map[string]int `yaml:"gpu_quota"`
}

type RuntimeConfig struct {
	Engine          string   `yaml:"engine"`
	Network         string   `yaml:"network"`
	AllowedImages   []string `yaml:"allowed_images"`
	DefaultTimeoutS int      `yaml:"default_timeout_seconds"`
}

type GPUConfig struct {
	Discovery string `yaml:"discovery"`
	MockCount int    `yaml:"mock_count"`
}

func LoadConfig(path string) (*Config, error) {
	raw, err := os.ReadFile(path)
	if err != nil {
		return nil, fmt.Errorf("read config: %w", err)
	}
	var cfg Config
	if err := yaml.Unmarshal(raw, &cfg); err != nil {
		return nil, fmt.Errorf("parse config: %w", err)
	}
	if cfg.Server.ListenAddr == "" {
		cfg.Server.ListenAddr = ":8088"
	}
	if cfg.Policy.MaxLeaseSeconds == 0 {
		cfg.Policy.MaxLeaseSeconds = 3600
	}
	if cfg.Policy.DefaultLeaseSecs == 0 {
		cfg.Policy.DefaultLeaseSecs = 900
	}
	if cfg.Policy.MaxConcurrent == 0 {
		cfg.Policy.MaxConcurrent = 1
	}
	if cfg.Runtime.Engine == "" {
		cfg.Runtime.Engine = "docker"
	}
	if cfg.Runtime.DefaultTimeoutS == 0 {
		cfg.Runtime.DefaultTimeoutS = 120
	}
	if cfg.GPU.Discovery == "" {
		cfg.GPU.Discovery = "nvml"
	}
	return &cfg, nil
}
