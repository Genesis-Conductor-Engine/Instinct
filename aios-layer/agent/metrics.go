package main

import (
	"fmt"
	"net/http"
	"sync/atomic"
)

type Metrics struct {
	leasesGranted uint64
	leasesReleased uint64
	launches       uint64
}

func NewMetrics() *Metrics {
	return &Metrics{}
}

func (m *Metrics) IncLeaseGranted() {
	atomic.AddUint64(&m.leasesGranted, 1)
}

func (m *Metrics) IncLeaseReleased() {
	atomic.AddUint64(&m.leasesReleased, 1)
}

func (m *Metrics) IncLaunches() {
	atomic.AddUint64(&m.launches, 1)
}

func (m *Metrics) Handler() http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		fmt.Fprintf(w, "aios_leases_granted_total %d\n", atomic.LoadUint64(&m.leasesGranted))
		fmt.Fprintf(w, "aios_leases_released_total %d\n", atomic.LoadUint64(&m.leasesReleased))
		fmt.Fprintf(w, "aios_container_launches_total %d\n", atomic.LoadUint64(&m.launches))
	})
}
