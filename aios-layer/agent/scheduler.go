package main

import (
	"errors"
	"fmt"
	"sync"
	"time"

	"github.com/google/uuid"
)

type Lease struct {
	ID        string    `json:"id"`
	User      string    `json:"user"`
	GPUIndex  int       `json:"gpu_index"`
	CreatedAt time.Time `json:"created_at"`
	ExpiresAt time.Time `json:"expires_at"`
}

type LeaseRequest struct {
	User          string `json:"user"`
	LeaseSeconds  int    `json:"lease_seconds"`
	RequestedGPU  int    `json:"requested_gpu"`
	AllowAnyGPU   bool   `json:"allow_any_gpu"`
	RequestReason string `json:"request_reason"`
}

type ReleaseRequest struct {
	User    string `json:"user"`
	LeaseID string `json:"lease_id"`
}

type LaunchRequest struct {
	User    string   `json:"user"`
	LeaseID string   `json:"lease_id"`
	Image   string   `json:"image"`
	Command []string `json:"command"`
	Env     []string `json:"env"`
	GPU     int      `json:"gpu"`
}

type Scheduler struct {
	policy PolicyConfig
	gpus   []GPUInfo
	leases map[string]Lease
	mu     sync.Mutex
}

func NewScheduler(policy PolicyConfig, gpus []GPUInfo) *Scheduler {
	return &Scheduler{
		policy: policy,
		gpus:   gpus,
		leases: make(map[string]Lease),
	}
}

func (s *Scheduler) GPUs() []GPUInfo {
	s.mu.Lock()
	defer s.mu.Unlock()
	return append([]GPUInfo{}, s.gpus...)
}

func (s *Scheduler) ListLeases() []Lease {
	s.mu.Lock()
	defer s.mu.Unlock()
	result := make([]Lease, 0, len(s.leases))
	for _, lease := range s.leases {
		result = append(result, lease)
	}
	return result
}

func (s *Scheduler) RequestLease(req LeaseRequest) (Lease, error) {
	s.mu.Lock()
	defer s.mu.Unlock()

	if !s.isAllowed(req.User) {
		return Lease{}, fmt.Errorf("user %s not allowed", req.User)
	}
	if len(s.leases) >= s.policy.MaxConcurrent {
		return Lease{}, errors.New("max concurrent leases reached")
	}
	leaseSeconds := req.LeaseSeconds
	if leaseSeconds <= 0 {
		leaseSeconds = s.policy.DefaultLeaseSecs
	}
	if leaseSeconds > s.policy.MaxLeaseSeconds {
		return Lease{}, fmt.Errorf("lease duration exceeds max %ds", s.policy.MaxLeaseSeconds)
	}

	gpuIndex, err := s.selectGPU(req)
	if err != nil {
		return Lease{}, err
	}

	lease := Lease{
		ID:        uuid.NewString(),
		User:      req.User,
		GPUIndex:  gpuIndex,
		CreatedAt: time.Now().UTC(),
		ExpiresAt: time.Now().UTC().Add(time.Duration(leaseSeconds) * time.Second),
	}
	s.leases[lease.ID] = lease
	return lease, nil
}

func (s *Scheduler) ReleaseLease(req ReleaseRequest) error {
	s.mu.Lock()
	defer s.mu.Unlock()
	lease, ok := s.leases[req.LeaseID]
	if !ok {
		return errors.New("lease not found")
	}
	if lease.User != req.User {
		return errors.New("lease owned by different user")
	}
	delete(s.leases, req.LeaseID)
	return nil
}

func (s *Scheduler) ValidateLaunch(user, leaseID string) error {
	_, err := s.LeaseGPU(user, leaseID)
	return err
}

func (s *Scheduler) LeaseGPU(user, leaseID string) (int, error) {
	s.mu.Lock()
	defer s.mu.Unlock()
	lease, ok := s.leases[leaseID]
	if !ok {
		return -1, errors.New("lease not found")
	}
	if lease.User != user {
		return -1, errors.New("lease owned by different user")
	}
	if time.Now().UTC().After(lease.ExpiresAt) {
		delete(s.leases, leaseID)
		return -1, errors.New("lease expired")
	}
	return lease.GPUIndex, nil
}

func (s *Scheduler) selectGPU(req LeaseRequest) (int, error) {
	if len(s.gpus) == 0 {
		return -1, errors.New("no GPUs available")
	}

	occupied := make(map[int]bool)
	for _, lease := range s.leases {
		occupied[lease.GPUIndex] = true
	}

	if req.RequestedGPU >= 0 && !req.AllowAnyGPU {
		if req.RequestedGPU >= len(s.gpus) {
			return -1, errors.New("requested gpu out of range")
		}
		if occupied[req.RequestedGPU] {
			return -1, errors.New("requested gpu already leased")
		}
		return req.RequestedGPU, nil
	}

	for _, gpu := range s.gpus {
		if !occupied[gpu.Index] {
			return gpu.Index, nil
		}
	}
	return -1, errors.New("no free GPUs available")
}

func (s *Scheduler) isAllowed(user string) bool {
	if len(s.policy.AllowedUsers) == 0 {
		return true
	}
	for _, allowed := range s.policy.AllowedUsers {
		if allowed == user {
			return true
		}
	}
	return false
}
