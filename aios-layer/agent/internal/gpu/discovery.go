package gpu

import (
	"bufio"
	"bytes"
	"errors"
	"os/exec"
	"strconv"
	"strings"
)

type GPU struct {
	Index       int    `json:"index"`
	Name        string `json:"name"`
	MemoryTotal int    `json:"memory_total_mb"`
}

func Discover() ([]GPU, error) {
	cmd := exec.Command("nvidia-smi", "--query-gpu=index,name,memory.total", "--format=csv,noheader,nounits")
	output, err := cmd.Output()
	if err != nil {
		return nil, errors.New("nvidia-smi not available")
	}
	return parseCSV(output)
}

func parseCSV(data []byte) ([]GPU, error) {
	var gpus []GPU
	scanner := bufio.NewScanner(bytes.NewReader(data))
	for scanner.Scan() {
		line := strings.TrimSpace(scanner.Text())
		if line == "" {
			continue
		}
		parts := strings.Split(line, ",")
		if len(parts) < 3 {
			continue
		}
		index, err := strconv.Atoi(strings.TrimSpace(parts[0]))
		if err != nil {
			continue
		}
		name := strings.TrimSpace(parts[1])
		mem, err := strconv.Atoi(strings.TrimSpace(parts[2]))
		if err != nil {
			continue
		}
		gpus = append(gpus, GPU{Index: index, Name: name, MemoryTotal: mem})
	}
	if err := scanner.Err(); err != nil {
		return nil, err
	}
	return gpus, nil
}
