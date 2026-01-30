package main

import (
	"context"
	"encoding/json"
	"errors"
	"flag"
	"log"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"
)

func main() {
	configPath := flag.String("config", "config/aios.yaml", "Path to config file")
	flag.Parse()

	cfg, err := LoadConfig(*configPath)
	if err != nil {
		log.Fatalf("load config: %v", err)
	}

	gpuInfo, err := DiscoverGPUs(cfg.GPU)
	if err != nil {
		log.Printf("gpu discovery warning: %v", err)
	}

	scheduler := NewScheduler(cfg.Policy, gpuInfo)
	runtime := NewRuntime(cfg.Runtime)
	metrics := NewMetrics()

	mux := http.NewServeMux()
	mux.HandleFunc("/v1/health", func(w http.ResponseWriter, r *http.Request) {
		writeJSON(w, http.StatusOK, map[string]string{"status": "ok"})
	})
	mux.HandleFunc("/v1/gpus", func(w http.ResponseWriter, r *http.Request) {
		writeJSON(w, http.StatusOK, scheduler.GPUs())
	})
	mux.HandleFunc("/v1/leases", func(w http.ResponseWriter, r *http.Request) {
		switch r.Method {
		case http.MethodPost:
			var req LeaseRequest
			if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
				writeError(w, http.StatusBadRequest, err)
				return
			}
			req.User = resolveUser(r, req.User)
			lease, err := scheduler.RequestLease(req)
			if err != nil {
				writeError(w, http.StatusForbidden, err)
				return
			}
			metrics.IncLeaseGranted()
			writeJSON(w, http.StatusCreated, lease)
		case http.MethodGet:
			writeJSON(w, http.StatusOK, scheduler.ListLeases())
		default:
			writeError(w, http.StatusMethodNotAllowed, errors.New("method not allowed"))
		}
	})
	mux.HandleFunc("/v1/leases/release", func(w http.ResponseWriter, r *http.Request) {
		if r.Method != http.MethodPost {
			writeError(w, http.StatusMethodNotAllowed, errors.New("method not allowed"))
			return
		}
		var req ReleaseRequest
		if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
			writeError(w, http.StatusBadRequest, err)
			return
		}
		req.User = resolveUser(r, req.User)
		if err := scheduler.ReleaseLease(req); err != nil {
			writeError(w, http.StatusForbidden, err)
			return
		}
		metrics.IncLeaseReleased()
		writeJSON(w, http.StatusOK, map[string]string{"status": "released"})
	})
	mux.HandleFunc("/v1/launch", func(w http.ResponseWriter, r *http.Request) {
		if r.Method != http.MethodPost {
			writeError(w, http.StatusMethodNotAllowed, errors.New("method not allowed"))
			return
		}
		var req LaunchRequest
		if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
			writeError(w, http.StatusBadRequest, err)
			return
		}
		req.User = resolveUser(r, req.User)
		gpuIndex, err := scheduler.LeaseGPU(req.User, req.LeaseID)
		if err != nil {
			writeError(w, http.StatusForbidden, err)
			return
		}
		req.GPU = gpuIndex
		result, err := runtime.Launch(req)
		if err != nil {
			writeError(w, http.StatusBadGateway, err)
			return
		}
		metrics.IncLaunches()
		writeJSON(w, http.StatusOK, result)
	})
	mux.Handle("/metrics", metrics.Handler())

	server := &http.Server{
		Addr:              cfg.Server.ListenAddr,
		Handler:           logRequests(mux),
		ReadHeaderTimeout: 5 * time.Second,
	}

	go func() {
		log.Printf("aios-agent listening on %s", cfg.Server.ListenAddr)
		if err := server.ListenAndServe(); err != nil && !errors.Is(err, http.ErrServerClosed) {
			log.Fatalf("listen: %v", err)
		}
	}()

	stop := make(chan os.Signal, 1)
	signal.Notify(stop, syscall.SIGINT, syscall.SIGTERM)
	<-stop

	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()
	if err := server.Shutdown(ctx); err != nil {
		log.Printf("shutdown error: %v", err)
	}
}

func resolveUser(r *http.Request, fallback string) string {
	if user := r.Header.Get("X-AIOS-User"); user != "" {
		return user
	}
	if fallback != "" {
		return fallback
	}
	return "local"
}

func logRequests(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		start := time.Now()
		next.ServeHTTP(w, r)
		log.Printf("%s %s %s", r.Method, r.URL.Path, time.Since(start))
	})
}

func writeJSON(w http.ResponseWriter, status int, payload any) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	if err := json.NewEncoder(w).Encode(payload); err != nil {
		log.Printf("write json: %v", err)
	}
}

func writeError(w http.ResponseWriter, status int, err error) {
	writeJSON(w, status, map[string]string{"error": err.Error()})
}
