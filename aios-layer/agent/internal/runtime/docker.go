package runtime

import (
	"fmt"
	"os/exec"
)

type DockerLauncher struct {
	Socket    string
	Image     string
	ModelPort int
}

func (d DockerLauncher) Launch(gpuIndex int) error {
	args := []string{
		"-H", d.Socket,
		"run", "--rm", "-d",
		"--gpus", fmt.Sprintf("device=%d", gpuIndex),
		"-p", fmt.Sprintf("%d:%d", d.ModelPort, d.ModelPort),
		d.Image,
	}
	cmd := exec.Command("docker", args...)
	return cmd.Run()
}
