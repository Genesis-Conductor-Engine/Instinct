package scheduler

import (
	"errors"
	"sync"
	"time"
)

type GPU struct {
	Index       int    `json:"index"`
	Name        string `json:"name"`
	MemoryTotal int    `json:"memory_total_mb"`
}

type Lease struct {
	ID        string    `json:"id"`
	GPUIndex  int       `json:"gpu_index"`
	User      string    `json:"user"`
	ExpiresAt time.Time `json:"expires_at"`
}

type Scheduler struct {
	mu     sync.Mutex
	gpus   []GPU
	leases map[string]Lease
}

func New(gpus []GPU) *Scheduler {
	return &Scheduler{gpus: gpus, leases: make(map[string]Lease)}
}

func (s *Scheduler) ListGPUs() []GPU {
	s.mu.Lock()
	defer s.mu.Unlock()
	return append([]GPU{}, s.gpus...)
}

func (s *Scheduler) ListLeases() []Lease {
	s.mu.Lock()
	defer s.mu.Unlock()
	leases := make([]Lease, 0, len(s.leases))
	for _, lease := range s.leases {
		leases = append(leases, lease)
	}
	return leases
}

func (s *Scheduler) ActiveLeasesForUser(user string) int {
	s.mu.Lock()
	defer s.mu.Unlock()
	count := 0
	for _, lease := range s.leases {
		if lease.User == user && time.Now().Before(lease.ExpiresAt) {
			count++
		}
	}
	return count
}

func (s *Scheduler) CreateLease(id string, user string, duration time.Duration) (Lease, error) {
	s.mu.Lock()
	defer s.mu.Unlock()
	available := s.availableGPUIndices()
	if len(available) == 0 {
		return Lease{}, errors.New("no gpus available")
	}
	lease := Lease{
		ID:        id,
		GPUIndex:  available[0],
		User:      user,
		ExpiresAt: time.Now().Add(duration),
	}
	s.leases[id] = lease
	return lease, nil
}

func (s *Scheduler) Release(id string) {
	s.mu.Lock()
	defer s.mu.Unlock()
	delete(s.leases, id)
}

func (s *Scheduler) ReapExpired() {
	s.mu.Lock()
	defer s.mu.Unlock()
	now := time.Now()
	for id, lease := range s.leases {
		if now.After(lease.ExpiresAt) {
			delete(s.leases, id)
		}
	}
}

func (s *Scheduler) availableGPUIndices() []int {
	used := make(map[int]bool)
	now := time.Now()
	for _, lease := range s.leases {
		if now.Before(lease.ExpiresAt) {
			used[lease.GPUIndex] = true
		}
	}
	var available []int
	for _, gpu := range s.gpus {
		if !used[gpu.Index] {
			available = append(available, gpu.Index)
		}
	}
	return available
}
