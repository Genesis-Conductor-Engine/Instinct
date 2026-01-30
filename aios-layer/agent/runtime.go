package main

import (
	"bytes"
	"errors"
	"fmt"
	"os/exec"
	"strings"
	"time"
)

type Runtime struct {
	cfg RuntimeConfig
}

type LaunchResult struct {
	Command string `json:"command"`
	Output  string `json:"output"`
}

func NewRuntime(cfg RuntimeConfig) *Runtime {
	return &Runtime{cfg: cfg}
}

func (r *Runtime) Launch(req LaunchRequest) (LaunchResult, error) {
	if !r.allowedImage(req.Image) {
		return LaunchResult{}, fmt.Errorf("image not allowed: %s", req.Image)
	}
	if r.cfg.Engine != "docker" && r.cfg.Engine != "podman" {
		return LaunchResult{}, errors.New("unsupported runtime engine")
	}
	args := []string{"run", "--rm"}
	if r.cfg.Network != "" {
		args = append(args, "--network", r.cfg.Network)
	}
	if req.GPU >= 0 {
		args = append(args, "--gpus", fmt.Sprintf("device=%d", req.GPU))
	}
	for _, env := range req.Env {
		args = append(args, "-e", env)
	}
	args = append(args, req.Image)
	args = append(args, req.Command...)
	cmd := exec.Command(r.cfg.Engine, args...)

	var stdout bytes.Buffer
	cmd.Stdout = &stdout
	cmd.Stderr = &stdout

	timeout := time.Duration(r.cfg.DefaultTimeoutS) * time.Second
	if timeout == 0 {
		timeout = 120 * time.Second
	}
	if err := runWithTimeout(cmd, timeout); err != nil {
		return LaunchResult{}, err
	}
	return LaunchResult{
		Command: fmt.Sprintf("%s %s", r.cfg.Engine, strings.Join(args, " ")),
		Output:  stdout.String(),
	}, nil
}

func (r *Runtime) allowedImage(image string) bool {
	if len(r.cfg.AllowedImages) == 0 {
		return true
	}
	for _, allowed := range r.cfg.AllowedImages {
		if allowed == image {
			return true
		}
	}
	return false
}

func runWithTimeout(cmd *exec.Cmd, timeout time.Duration) error {
	if err := cmd.Start(); err != nil {
		return fmt.Errorf("start runtime: %w", err)
	}
	done := make(chan error, 1)
	go func() {
		done <- cmd.Wait()
	}()
	select {
	case err := <-done:
		if err != nil {
			return fmt.Errorf("runtime error: %w", err)
		}
		return nil
	case <-time.After(timeout):
		_ = cmd.Process.Kill()
		return fmt.Errorf("runtime timeout after %s", timeout)
	}
}
