package main

import "testing"

func TestSchedulerLeaseLifecycle(t *testing.T) {
	policy := PolicyConfig{
		AllowedUsers:     []string{"alice"},
		MaxLeaseSeconds:  60,
		DefaultLeaseSecs: 30,
		MaxConcurrent:    1,
	}
	gpus := []GPUInfo{{Index: 0, Name: "GPU0"}}
	scheduler := NewScheduler(policy, gpus)

	lease, err := scheduler.RequestLease(LeaseRequest{User: "alice"})
	if err != nil {
		t.Fatalf("expected lease, got error: %v", err)
	}
	if lease.GPUIndex != 0 {
		t.Fatalf("expected gpu 0, got %d", lease.GPUIndex)
	}

	if _, err := scheduler.RequestLease(LeaseRequest{User: "alice"}); err == nil {
		t.Fatalf("expected max concurrent error")
	}

	if err := scheduler.ReleaseLease(ReleaseRequest{User: "alice", LeaseID: lease.ID}); err != nil {
		t.Fatalf("expected release, got error: %v", err)
	}
}

func TestSchedulerRejectsUnauthorized(t *testing.T) {
	policy := PolicyConfig{
		AllowedUsers:     []string{"alice"},
		MaxLeaseSeconds:  60,
		DefaultLeaseSecs: 30,
		MaxConcurrent:    1,
	}
	scheduler := NewScheduler(policy, []GPUInfo{{Index: 0}})

	if _, err := scheduler.RequestLease(LeaseRequest{User: "bob"}); err == nil {
		t.Fatalf("expected unauthorized error")
	}
}
