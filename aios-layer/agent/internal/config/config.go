package config

import (
	"os"

	"gopkg.in/yaml.v3"
)

type Config struct {
	Server    ServerConfig    `yaml:"server"`
	Policy    PolicyConfig    `yaml:"policy"`
	Scheduler SchedulerConfig `yaml:"scheduler"`
	Runtime   RuntimeConfig   `yaml:"runtime"`
	Model     ModelConfig     `yaml:"model"`
	Metrics   MetricsConfig   `yaml:"metrics"`
}

type ServerConfig struct {
	ListenAddress string `yaml:"listen_address"`
}

type PolicyConfig struct {
	MaxGPUsPerUser int `yaml:"max_gpus_per_user"`
	MaxDurationSec int `yaml:"max_duration_sec"`
}

type SchedulerConfig struct {
	LeaseTTLSeconds int `yaml:"lease_ttl_seconds"`
}

type RuntimeConfig struct {
	DockerSocket string `yaml:"docker_socket"`
	ModelImage   string `yaml:"model_image"`
	ModelPort    int    `yaml:"model_port"`
	EnableLaunch bool   `yaml:"enable_launch"`
}

type ModelConfig struct {
	Endpoint string `yaml:"endpoint"`
}

type MetricsConfig struct {
	Enabled bool `yaml:"enabled"`
}

func Load(path string) (Config, error) {
	data, err := os.ReadFile(path)
	if err != nil {
		return Config{}, err
	}
	var cfg Config
	if err := yaml.Unmarshal(data, &cfg); err != nil {
		return Config{}, err
	}
	return cfg, nil
}
