package scheduler

import (
	"testing"
	"time"
)

func TestCreateLeaseExclusive(t *testing.T) {
	gpus := []GPU{{Index: 0, Name: "gpu0", MemoryTotal: 1000}, {Index: 1, Name: "gpu1", MemoryTotal: 1000}}
	sched := New(gpus)
	lease1, err := sched.CreateLease("lease1", "user", time.Second)
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	lease2, err := sched.CreateLease("lease2", "user", time.Second)
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if lease1.GPUIndex == lease2.GPUIndex {
		t.Fatalf("expected exclusive GPU assignment")
	}
}

func TestReapExpired(t *testing.T) {
	gpus := []GPU{{Index: 0, Name: "gpu0", MemoryTotal: 1000}}
	sched := New(gpus)
	_, err := sched.CreateLease("lease1", "user", time.Millisecond)
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	time.Sleep(time.Millisecond * 2)
	sched.ReapExpired()
	if len(sched.ListLeases()) != 0 {
		t.Fatalf("expected expired lease to be reaped")
	}
}
