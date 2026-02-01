package scheduler

import (
	"testing"
	"time"
)

func BenchmarkCreateLease(b *testing.B) {
	gpus := []GPU{{Index: 0, Name: "gpu0", MemoryTotal: 1000}, {Index: 1, Name: "gpu1", MemoryTotal: 1000}}
	for i := 0; i < b.N; i++ {
		sched := New(gpus)
		_, _ = sched.CreateLease("lease", "user", time.Second)
	}
}

func BenchmarkReapExpired(b *testing.B) {
	gpus := []GPU{{Index: 0, Name: "gpu0", MemoryTotal: 1000}}
	for i := 0; i < b.N; i++ {
		sched := New(gpus)
		_, _ = sched.CreateLease("lease", "user", time.Nanosecond)
		sched.ReapExpired()
	}
}
