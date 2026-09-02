package tests

import (
	"testing"

	"github.com/llm-observability/platform/packages/configs/llm-obs-infra/service-discovery/discovery"
	"github.com/llm-observability/platform/packages/configs/llm-obs-infra/service-discovery/registry"
)

func TestResolveHealthy(t *testing.T) {
	reg := newTestRegistry()
	reg.Register(newTestInstance("resolve-svc", "localhost", 8080))

	disc := discovery.NewDiscovery(reg)

	inst, err := disc.Resolve("resolve-svc")
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if inst.Port != 8080 {
		t.Fatalf("expected port 8080, got %d", inst.Port)
	}
}

func TestResolveEndpoint(t *testing.T) {
	reg := newTestRegistry()
	reg.Register(newTestInstance("resolve-svc", "localhost", 8080))

	disc := discovery.NewDiscovery(reg)

	endpoint, err := disc.ResolveEndpoint("resolve-svc")
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if endpoint != "http://localhost:8080" {
		t.Fatalf("expected http://localhost:8080, got %s", endpoint)
	}
}

func TestResolveNoInstances(t *testing.T) {
	reg := newTestRegistry()
	disc := discovery.NewDiscovery(reg)

	_, err := disc.Resolve("nonexistent")
	if err == nil {
		t.Fatal("expected error for nonexistent service")
	}
}

func TestResolveAllUnhealthy(t *testing.T) {
	reg := newTestRegistry()
	inst := reg.Register(newTestInstance("unhealthy-svc", "localhost", 8080))
	reg.UpdateStatus("unhealthy-svc", inst.ID, registry.StatusUnhealthy, "TCP probe failed")

	disc := discovery.NewDiscovery(reg)

	_, err := disc.Resolve("unhealthy-svc")
	if err == nil {
		t.Fatal("expected error when all instances are unhealthy")
	}
}

func TestResolveAllReturnsMultiple(t *testing.T) {
	reg := newTestRegistry()
	reg.Register(newTestInstance("multi-svc", "localhost", 8080))
	reg.Register(newTestInstance("multi-svc", "localhost", 8081))

	disc := discovery.NewDiscovery(reg)

	instances, err := disc.ResolveAll("multi-svc")
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if len(instances) != 2 {
		t.Fatalf("expected 2 instances, got %d", len(instances))
	}
}

func TestListServices(t *testing.T) {
	reg := newTestRegistry()
	reg.Register(newTestInstance("svc-a", "localhost", 8080))
	reg.Register(newTestInstance("svc-b", "localhost", 8081))

	disc := discovery.NewDiscovery(reg)

	services := disc.ListServices()
	if len(services) != 2 {
		t.Fatalf("expected 2 services, got %d", len(services))
	}
}
