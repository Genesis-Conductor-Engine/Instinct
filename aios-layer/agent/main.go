package main

import (
	"encoding/json"
	"flag"
	"fmt"
	"log"
	"math/rand"
	"net/http"
	"strings"
	"time"

	"aios-layer/agent/internal/config"
	"aios-layer/agent/internal/gpu"
	"aios-layer/agent/internal/policy"
	"aios-layer/agent/internal/runtime"
	"aios-layer/agent/internal/scheduler"
)

type leaseRequest struct {
	User            string `json:"user"`
	DurationSeconds int    `json:"duration_seconds"`
	LaunchRuntime   bool   `json:"launch_runtime"`
}

type leaseResponse struct {
	Lease scheduler.Lease `json:"lease"`
}

func main() {
	configPath := flag.String("config", "../config/aios.yaml", "Path to config file")
	flag.Parse()

	cfg, err := config.Load(*configPath)
	if err != nil {
		log.Fatalf("failed to load config: %v", err)
	}

	gpus, err := gpu.Discover()
	if err != nil {
		log.Printf("gpu discovery failed: %v; falling back to CPU-only mode", err)
	}
	if len(gpus) == 0 {
		gpus = append(gpus, gpu.GPU{Index: -1, Name: "CPU", MemoryTotal: 0})
	}
	var schedGPUs []scheduler.GPU
	for _, g := range gpus {
		schedGPUs = append(schedGPUs, scheduler.GPU{Index: g.Index, Name: g.Name, MemoryTotal: g.MemoryTotal})
	}
	sched := scheduler.New(schedGPUs)
	policyCfg := policy.Policy{MaxGPUsPerUser: cfg.Policy.MaxGPUsPerUser, MaxDurationSec: cfg.Policy.MaxDurationSec}
	launcher := runtime.DockerLauncher{Socket: cfg.Runtime.DockerSocket, Image: cfg.Runtime.ModelImage, ModelPort: cfg.Runtime.ModelPort}

	go func() {
		ticker := time.NewTicker(time.Second * 5)
		for range ticker.C {
			sched.ReapExpired()
		}
	}()

	http.HandleFunc("/v1/health", func(w http.ResponseWriter, _ *http.Request) {
		w.WriteHeader(http.StatusOK)
		w.Write([]byte("ok"))
	})

	http.HandleFunc("/v1/gpus", func(w http.ResponseWriter, _ *http.Request) {
		writeJSON(w, sched.ListGPUs())
	})

	http.HandleFunc("/v1/leases", func(w http.ResponseWriter, r *http.Request) {
		switch r.Method {
		case http.MethodGet:
			writeJSON(w, sched.ListLeases())
		case http.MethodPost:
			var req leaseRequest
			if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
				writeError(w, http.StatusBadRequest, "invalid request body")
				return
			}
			if req.User == "" {
				req.User = "anonymous"
			}
			active := sched.ActiveLeasesForUser(req.User)
			if err := policyCfg.ValidateRequest(active, req.DurationSeconds); err != nil {
				writeError(w, http.StatusForbidden, err.Error())
				return
			}
			leaseID := fmt.Sprintf("lease-%d", rand.Intn(1_000_000))
			lease, err := sched.CreateLease(leaseID, req.User, time.Duration(req.DurationSeconds)*time.Second)
			if err != nil {
				writeError(w, http.StatusConflict, err.Error())
				return
			}
			if req.LaunchRuntime && cfg.Runtime.EnableLaunch {
				if lease.GPUIndex < 0 {
					log.Printf("runtime launch skipped: CPU-only mode")
				} else if err := launcher.Launch(lease.GPUIndex); err != nil {
					log.Printf("failed to launch runtime: %v", err)
				}
			}
			writeJSON(w, leaseResponse{Lease: lease})
		default:
			writeError(w, http.StatusMethodNotAllowed, "method not allowed")
		}
	})

	http.HandleFunc("/v1/leases/", func(w http.ResponseWriter, r *http.Request) {
		if r.Method != http.MethodDelete {
			writeError(w, http.StatusMethodNotAllowed, "method not allowed")
			return
		}
		id := strings.TrimPrefix(r.URL.Path, "/v1/leases/")
		if id == "" {
			writeError(w, http.StatusBadRequest, "missing lease id")
			return
		}
		sched.Release(id)
		w.WriteHeader(http.StatusNoContent)
	})

	http.HandleFunc("/metrics", func(w http.ResponseWriter, _ *http.Request) {
		if !cfg.Metrics.Enabled {
			w.WriteHeader(http.StatusNotFound)
			return
		}
		metrics := "# HELP aios_leases Active leases\n# TYPE aios_leases gauge\n"
		metrics += fmt.Sprintf("aios_leases %d\n", len(sched.ListLeases()))
		w.Write([]byte(metrics))
	})

	log.Printf("aios-agent listening on %s", cfg.Server.ListenAddress)
	log.Fatal(http.ListenAndServe(cfg.Server.ListenAddress, nil))
}

func writeJSON(w http.ResponseWriter, payload any) {
	w.Header().Set("Content-Type", "application/json")
	encoder := json.NewEncoder(w)
	if err := encoder.Encode(payload); err != nil {
		writeError(w, http.StatusInternalServerError, "encode error")
	}
}

func writeError(w http.ResponseWriter, status int, msg string) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	json.NewEncoder(w).Encode(map[string]string{"error": msg})
}
