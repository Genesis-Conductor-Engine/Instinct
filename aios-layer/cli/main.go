package main

import (
	"bytes"
	"encoding/json"
	"flag"
	"fmt"
	"net/http"
	"os"
	"time"
)

type inferRequest struct {
	Model string `json:"model"`
	Prompt string `json:"prompt"`
	MaxTokens int `json:"max_tokens"`
}

func main() {
	var (
		endpoint = flag.String("endpoint", "http://localhost:8000/v1/completions", "OpenAI-compatible completions endpoint")
		model    = flag.String("model", "TinyLlama/TinyLlama-1.1B-Chat-v1.0", "Model name")
		prompt   = flag.String("prompt", "Hello from aiosctl", "Prompt")
		maxTokens = flag.Int("max-tokens", 64, "Max tokens")
		timeout  = flag.Duration("timeout", 30*time.Second, "Request timeout")
	)
	flag.Parse()

	payload := inferRequest{
		Model: *model,
		Prompt: *prompt,
		MaxTokens: *maxTokens,
	}

	body, err := json.Marshal(payload)
	if err != nil {
		fmt.Printf("encode payload: %v\n", err)
		os.Exit(1)
	}

	req, err := http.NewRequest(http.MethodPost, *endpoint, bytes.NewBuffer(body))
	if err != nil {
		fmt.Printf("build request: %v\n", err)
		os.Exit(1)
	}
	req.Header.Set("Content-Type", "application/json")

	client := &http.Client{Timeout: *timeout}
	resp, err := client.Do(req)
	if err != nil {
		fmt.Printf("request error: %v\n", err)
		os.Exit(1)
	}
	defer resp.Body.Close()
	if resp.StatusCode >= 300 {
		fmt.Printf("request failed: %s\n", resp.Status)
		os.Exit(1)
	}

	var output map[string]any
	if err := json.NewDecoder(resp.Body).Decode(&output); err != nil {
		fmt.Printf("decode response: %v\n", err)
		os.Exit(1)
	}
	pretty, _ := json.MarshalIndent(output, "", "  ")
	fmt.Println(string(pretty))
}
