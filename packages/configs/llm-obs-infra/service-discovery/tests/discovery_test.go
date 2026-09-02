package tests

import (
	"testing"
	"time"

	"github.com/llm-observability/platform/packages/configs/llm-obs-infra/service-discovery/discovery"
	"github.com/llm-observability/platform/packages/configs/llm-obs-infra/service-discovery/registry"
)

func TestDiscoveryResolutionAndFallback(t *testing.T) {
	reg := registry.NewRegistry(registry.DefaultInstanceDefaults)
	disc := discovery.NewDiscovery(reg)

	// 1. Resolve unregistered service -> should fail with diagnostic error
	_, err := disc.Resolve("ai-service")
	if err == nil {
		t.Fatalf("expected error for unregistered service, got nil")
	}

	// 2. ResolveWithFallback for unregistered service -> should return fallback instance
	inst, fallbackUsed := disc.ResolveWithFallback("ai-service", "legacy-ai-host", 8080, "http")
	if !fallbackUsed {
		t.Errorf("expected fallbackUsed: true, got false")
	}
	if inst.Host != "legacy-ai-host" || inst.Port != 8080 {
		t.Errorf("expected fallback host/port legacy-ai-host:8080, got %s:%d", inst.Host, inst.Port)
	}

	// 3. Register service -> Resolve should succeed without fallback
	reg.Register(&registry.ServiceInstance{
		Name:     "ai-service",
		Host:     "ai-container",
		Port:     9000,
		Protocol: "http",
	})

	instResolved, fallbackUsed2 := disc.ResolveWithFallback("ai-service", "legacy-ai-host", 8080, "http")
	if fallbackUsed2 {
		t.Errorf("expected fallbackUsed: false for registered service, got true")
	}
	if instResolved.Host != "ai-container" || instResolved.Port != 9000 {
		t.Errorf("expected resolved host/port ai-container:9000, got %s:%d", instResolved.Host, instResolved.Port)
	}
}

func TestDiscoveryWatchEventStream(t *testing.T) {
	reg := registry.NewRegistry(registry.DefaultInstanceDefaults)
	disc := discovery.NewDiscovery(reg)

	events := disc.Watch("watch-service")

	reg.Register(&registry.ServiceInstance{
		Name:     "watch-service",
		Host:     "localhost",
		Port:     8000,
		Protocol: "http",
	})

	select {
	case evt := <-events:
		if evt.Instance.Name != "watch-service" {
			t.Errorf("expected event for watch-service, got %s", evt.Instance.Name)
		}
	case <-time.After(2 * time.Second):
		t.Fatalf("timed out waiting for watch event")
	}
}
