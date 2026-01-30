package main

import (
	"fmt"

	"github.com/NVIDIA/go-nvml/pkg/nvml"
)

type GPUInfo struct {
	Index       int    `json:"index"`
	UUID        string `json:"uuid"`
	Name        string `json:"name"`
	MemoryTotal uint64 `json:"memory_total_bytes"`
}

func DiscoverGPUs(cfg GPUConfig) ([]GPUInfo, error) {
	if cfg.Discovery == "mock" {
		return mockGPUs(cfg.MockCount), nil
	}
	if ret := nvml.Init(); ret != nvml.SUCCESS {
		if cfg.MockCount > 0 {
			return mockGPUs(cfg.MockCount), fmt.Errorf("nvml init failed: %s, using mock", nvml.ErrorString(ret))
		}
		return nil, fmt.Errorf("nvml init failed: %s", nvml.ErrorString(ret))
	}
	defer nvml.Shutdown()

	count, ret := nvml.DeviceGetCount()
	if ret != nvml.SUCCESS {
		return nil, fmt.Errorf("nvml device count failed: %s", nvml.ErrorString(ret))
	}
	if count == 0 {
		if cfg.MockCount > 0 {
			return mockGPUs(cfg.MockCount), fmt.Errorf("no gpus found, using mock")
		}
		return []GPUInfo{}, nil
	}
	gpus := make([]GPUInfo, 0, count)
	for i := 0; i < count; i++ {
		device, ret := nvml.DeviceGetHandleByIndex(i)
		if ret != nvml.SUCCESS {
			return nil, fmt.Errorf("nvml device handle failed: %s", nvml.ErrorString(ret))
		}
		uuid, _ := device.GetUUID()
		name, _ := device.GetName()
		mem, _ := device.GetMemoryInfo()
		gpus = append(gpus, GPUInfo{
			Index:       i,
			UUID:        uuid,
			Name:        name,
			MemoryTotal: mem.Total,
		})
	}
	return gpus, nil
}

func mockGPUs(count int) []GPUInfo {
	gpus := make([]GPUInfo, 0, count)
	for i := 0; i < count; i++ {
		gpus = append(gpus, GPUInfo{
			Index:       i,
			UUID:        fmt.Sprintf("MOCK-%d", i),
			Name:        "Mock GPU",
			MemoryTotal: 24 * 1024 * 1024 * 1024,
		})
	}
	return gpus
}
