package tests

import (
	"context"
	"net"
	"net/http"
	"net/http/httptest"
	"testing"
	"time"

	"github.com/llm-observability/platform/packages/configs/llm-obs-infra/service-discovery/registry"
)

func TestHealthProberHTTP(t *testing.T) {
	ts := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Path == "/health" {
			w.WriteHeader(http.StatusOK)
		} else {
			w.WriteHeader(http.StatusInternalServerError)
		}
	}))
	defer ts.Close()

	host, portStr, err := net.SplitHostPort(ts.Listener.Addr().String())
	if err != nil {
		t.Fatalf("failed to parse test server host/port: %v", err)
	}
	var port int
	_, _ = fmtSscanf(portStr, "%d", &port)

	reg := registry.NewRegistry(registry.DefaultInstanceDefaults)
	inst := &registry.ServiceInstance{
		Name: "test-http-svc",
		Host: host,
		Port: port,
		HealthCheck: registry.HealthCheckSpec{
			Protocol:         "http",
			Path:             "/health",
			Timeout:          1 * time.Second,
			FailureThreshold: 2,
			SuccessThreshold: 1,
		},
	}
	registered := reg.Register(inst)

	prober := registry.NewHealthProber(reg, registry.HealthProberConfig{
		MaxConcurrent:    5,
		DefaultFailureTh: 2,
		DefaultSuccessTh: 1,
	})

	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()

	reg.UpdateStatus(registered.Name, registered.ID, registry.StatusUnhealthy, "initial error")
	if registered.Status != registry.StatusUnhealthy {
		t.Fatalf("expected status UNHEALTHY, got %s", registered.Status)
	}

	prober.Start(ctx)
}

func fmtSscanf(str string, format string, a ...interface{}) (int, error) {
	var val int
	for _, ch := range str {
		if ch >= '0' && ch <= '9' {
			val = val*10 + int(ch-'0')
		}
	}
	if len(a) > 0 {
		if p, ok := a[0].(*int); ok {
			*p = val
		}
	}
	return 1, nil
}

func TestHealthProberThresholds(t *testing.T) {
	reg := registry.NewRegistry(registry.DefaultInstanceDefaults)
	inst := reg.Register(&registry.ServiceInstance{
		Name: "flapping-svc",
		Host: "127.0.0.1",
		Port: 59999, // unopened port
		HealthCheck: registry.HealthCheckSpec{
			Protocol:         "tcp",
			Timeout:          100 * time.Millisecond,
			FailureThreshold: 3,
			SuccessThreshold: 2,
		},
	})

	if inst.Status != registry.StatusHealthy {
		t.Fatalf("expected initial status HEALTHY, got %s", inst.Status)
	}

	prober := registry.NewHealthProber(reg, registry.HealthProberConfig{
		DefaultFailureTh: 3,
		DefaultSuccessTh: 2,
	})

	prober.Start(context.Background())
}
