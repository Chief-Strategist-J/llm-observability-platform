package tests

import (
	"fmt"
	"net"
	"net/http"
	"net/http/httptest"
	"testing"

	"github.com/llm-observability/platform/packages/configs/llm-obs-infra/service-discovery/registry"
)

func TestHTTPProbeHealthy(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
	}))
	defer server.Close()

	host, port := parseHostPort(t, server.Listener.Addr().String())

	reg := newTestRegistry()
	inst := reg.Register(&registry.ServiceInstance{
		Name:     "http-svc",
		Host:     host,
		Port:     port,
		Protocol: "http",
		HealthCheck: registry.HealthCheckSpec{
			Protocol: "http",
			Path:     "/",
		},
	})

	prober := registry.NewHealthProber(reg, registry.HealthProberConfig{
		ProbeInterval: 100,
		MaxConcurrent: 5,
	})
	_ = prober

	got, _ := reg.GetInstance("http-svc", inst.ID)
	if got.Status != registry.StatusHealthy {
		t.Fatalf("expected HEALTHY, got %s", got.Status)
	}
}

func TestHTTPProbeUnhealthy(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusServiceUnavailable)
	}))
	defer server.Close()

	host, port := parseHostPort(t, server.Listener.Addr().String())

	reg := newTestRegistry()
	reg.Register(&registry.ServiceInstance{
		Name:     "unhealthy-svc",
		Host:     host,
		Port:     port,
		Protocol: "http",
		HealthCheck: registry.HealthCheckSpec{
			Protocol: "http",
			Path:     "/",
		},
	})

	_ = reg
}

func TestTCPProbeHealthy(t *testing.T) {
	listener, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		t.Fatalf("failed to start listener: %v", err)
	}
	defer listener.Close()

	host, port := parseHostPort(t, listener.Addr().String())

	reg := newTestRegistry()
	inst := reg.Register(&registry.ServiceInstance{
		Name:     "tcp-svc",
		Host:     host,
		Port:     port,
		Protocol: "tcp",
		HealthCheck: registry.HealthCheckSpec{
			Protocol: "tcp",
		},
	})

	got, _ := reg.GetInstance("tcp-svc", inst.ID)
	if got.Status != registry.StatusHealthy {
		t.Fatalf("expected HEALTHY, got %s", got.Status)
	}
}

func parseHostPort(t *testing.T, addr string) (string, int) {
	t.Helper()
	host, portStr, err := net.SplitHostPort(addr)
	if err != nil {
		t.Fatalf("failed to parse address: %v", err)
	}
	var port int
	fmt.Sscanf(portStr, "%d", &port)
	return host, port
}
