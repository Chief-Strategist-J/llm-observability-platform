package tests

import (
	"sync"
	"testing"

	"github.com/llm-observability/platform/packages/configs/llm-obs-infra/service-discovery/registry"
)

func newTestRegistry() *registry.Registry {
	return registry.NewRegistry(registry.DefaultInstanceDefaults)
}

func newTestInstance(name, host string, port int) *registry.ServiceInstance {
	return &registry.ServiceInstance{
		Name:     name,
		Host:     host,
		Port:     port,
		Protocol: "http",
		HealthCheck: registry.HealthCheckSpec{
			Protocol: "http",
			Path:     "/health",
		},
	}
}

func TestRegister(t *testing.T) {
	reg := newTestRegistry()
	inst := newTestInstance("test-svc", "localhost", 8080)

	registered := reg.Register(inst)

	if registered.ID == "" {
		t.Fatal("expected auto-generated ID")
	}
	if registered.Status != registry.StatusHealthy {
		t.Fatalf("expected HEALTHY, got %s", registered.Status)
	}
	if registered.Weight != 100 {
		t.Fatalf("expected default weight 100, got %d", registered.Weight)
	}
}

func TestDeregister(t *testing.T) {
	reg := newTestRegistry()
	inst := reg.Register(newTestInstance("test-svc", "localhost", 8080))

	err := reg.Deregister("test-svc", inst.ID)
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}

	all := reg.GetAll("test-svc")
	if len(all) != 0 {
		t.Fatalf("expected 0 instances, got %d", len(all))
	}
}

func TestDeregisterNotFound(t *testing.T) {
	reg := newTestRegistry()

	err := reg.Deregister("nonexistent", "fake-id")
	if err == nil {
		t.Fatal("expected error for nonexistent service")
	}
}

func TestGetHealthy(t *testing.T) {
	reg := newTestRegistry()
	inst1 := reg.Register(newTestInstance("test-svc", "localhost", 8080))
	reg.Register(newTestInstance("test-svc", "localhost", 8081))

	reg.UpdateStatus("test-svc", inst1.ID, registry.StatusUnhealthy, "probe failed")

	healthy := reg.GetHealthy("test-svc")
	if len(healthy) != 1 {
		t.Fatalf("expected 1 healthy instance, got %d", len(healthy))
	}
	if healthy[0].Port != 8081 {
		t.Fatalf("expected port 8081, got %d", healthy[0].Port)
	}
}

func TestGetAllServices(t *testing.T) {
	reg := newTestRegistry()
	reg.Register(newTestInstance("svc-a", "localhost", 8080))
	reg.Register(newTestInstance("svc-b", "localhost", 8081))
	reg.Register(newTestInstance("svc-b", "localhost", 8082))

	services := reg.GetAllServices()
	if len(services) != 2 {
		t.Fatalf("expected 2 services, got %d", len(services))
	}
	if len(services["svc-b"]) != 2 {
		t.Fatalf("expected 2 instances for svc-b, got %d", len(services["svc-b"]))
	}
}

func TestSubscribeReceivesEvents(t *testing.T) {
	reg := newTestRegistry()
	ch := reg.Subscribe()

	reg.Register(newTestInstance("test-svc", "localhost", 8080))

	event := <-ch
	if event.Type != registry.EventRegistered {
		t.Fatalf("expected REGISTERED event, got %s", event.Type)
	}
	if event.Instance.Name != "test-svc" {
		t.Fatalf("expected test-svc, got %s", event.Instance.Name)
	}

	reg.Unsubscribe(ch)
}

func TestConcurrentRegistration(t *testing.T) {
	reg := newTestRegistry()

	var wg sync.WaitGroup
	for i := 0; i < 100; i++ {
		wg.Add(1)
		go func(port int) {
			defer wg.Done()
			reg.Register(newTestInstance("concurrent-svc", "localhost", port))
		}(8000 + i)
	}
	wg.Wait()

	all := reg.GetAll("concurrent-svc")
	if len(all) != 100 {
		t.Fatalf("expected 100 instances, got %d", len(all))
	}
}

func TestEvictInstance(t *testing.T) {
	reg := newTestRegistry()
	ch := reg.Subscribe()

	inst := reg.Register(newTestInstance("test-svc", "localhost", 8080))
	<-ch

	reg.EvictInstance("test-svc", inst.ID)

	event := <-ch
	if event.Type != registry.EventHeartbeatExpired {
		t.Fatalf("expected HEARTBEAT_EXPIRED event, got %s", event.Type)
	}

	all := reg.GetAll("test-svc")
	if len(all) != 0 {
		t.Fatalf("expected 0 instances after eviction, got %d", len(all))
	}

	reg.Unsubscribe(ch)
}
