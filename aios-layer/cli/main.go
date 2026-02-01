package main

import (
	"bytes"
	"encoding/json"
	"flag"
	"fmt"
	"io"
	"net/http"
	"os"
	"time"
)

type leaseRequest struct {
	User            string `json:"user"`
	DurationSeconds int    `json:"duration_seconds"`
	LaunchRuntime   bool   `json:"launch_runtime"`
}

type leaseResponse struct {
	Lease struct {
		ID       string `json:"id"`
		GPUIndex int    `json:"gpu_index"`
	} `json:"lease"`
}

type openAIRequest struct {
	Model    string   `json:"model"`
	Messages []string `json:"messages"`
}

func main() {
	if len(os.Args) < 2 {
		usage()
		return
	}

	switch os.Args[1] {
	case "lease":
		leaseCmd := flag.NewFlagSet("lease", flag.ExitOnError)
		agent := leaseCmd.String("agent", "http://127.0.0.1:8080", "agent address")
		user := leaseCmd.String("user", "demo", "user name")
		duration := leaseCmd.Int("duration", 300, "lease duration in seconds")
		launch := leaseCmd.Bool("launch", false, "launch runtime")
		leaseCmd.Parse(os.Args[2:])
		requestLease(*agent, *user, *duration, *launch)
	case "infer":
		inferCmd := flag.NewFlagSet("infer", flag.ExitOnError)
		endpoint := inferCmd.String("endpoint", "http://127.0.0.1:8000/v1/chat/completions", "model endpoint")
		model := inferCmd.String("model", "TinyLlama/TinyLlama-1.1B-Chat-v1.0", "model name")
		prompt := inferCmd.String("prompt", "Hello", "prompt")
		inferCmd.Parse(os.Args[2:])
		sendInference(*endpoint, *model, *prompt)
	default:
		usage()
	}
}

func usage() {
	fmt.Println("Usage: aiosctl <lease|infer> [flags]")
}

func requestLease(agent, user string, duration int, launch bool) {
	payload := leaseRequest{User: user, DurationSeconds: duration, LaunchRuntime: launch}
	body, _ := json.Marshal(payload)
	resp, err := http.Post(agent+"/v1/leases", "application/json", bytes.NewReader(body))
	if err != nil {
		fmt.Printf("error: %v\n", err)
		return
	}
	defer resp.Body.Close()
	data, _ := io.ReadAll(resp.Body)
	fmt.Println(string(data))
}

func sendInference(endpoint, model, prompt string) {
	payload := map[string]any{
		"model": model,
		"messages": []map[string]string{
			{"role": "user", "content": prompt},
		},
		"max_tokens": 64,
		"temperature": 0.2,
	}
	body, _ := json.Marshal(payload)
	client := http.Client{Timeout: time.Second * 60}
	resp, err := client.Post(endpoint, "application/json", bytes.NewReader(body))
	if err != nil {
		fmt.Printf("error: %v\n", err)
		return
	}
	defer resp.Body.Close()
	data, _ := io.ReadAll(resp.Body)
	fmt.Println(string(data))
}
