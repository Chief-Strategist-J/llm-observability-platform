package tests

import (
	"testing"

	"github.com/llm-observability/platform/packages/configs/llm-obs-infra/service-discovery/discovery"
	"github.com/llm-observability/platform/packages/configs/llm-obs-infra/service-discovery/registry"
)

func TestDiscoveryResolutionAndLKG(t *testing.T) {
	reg := registry.NewRegistry(registry.DefaultInstanceDefaults)
	disc := discovery.NewDiscovery(reg)

	// 1. Resolve unregistered service -> should fail with diagnostic error
	_, err := disc.Resolve("ai-service")
	if err == nil {
		t.Fatalf("expected error for unregistered service, got nil")
	}

	// 2. Register service -> Resolve should succeed
	reg.Register(&registry.ServiceInstance{
		Name:     "ai-service",
		Host:     "ai-container",
		Port:     9000,
		Protocol: "http",
	})

	instResolved, err := disc.Resolve("ai-service")
	if err != nil {
		t.Fatalf("expected resolved instance, got error: %v", err)
	}
	if instResolved.Host != "ai-container" || instResolved.Port != 9000 {
		t.Errorf("expected resolved host/port ai-container:9000, got %s:%d", instResolved.Host, instResolved.Port)
	}

	// 3. Test LKG caching when service is updated to unhealthy
	reg.UpdateStatus("ai-service", instResolved.ID, registry.StatusUnhealthy, "transient error")
	
	// Direct resolve should fail
	_, err = disc.Resolve("ai-service")
	if err == nil {
		t.Fatalf("expected resolve to fail when service is unhealthy")
	}

	// LKG resolution should return cached instances with lkgUsed=true
	lkgInstances, lkgUsed, err := disc.ResolveWithLKG("ai-service")
	if err != nil || !lkgUsed || len(lkgInstances) == 0 {
		t.Fatalf("expected LKG resolution to return cached topology, got lkgUsed=%v, err=%v", lkgUsed, err)
	}
	if lkgInstances[0].Host != "ai-container" {
		t.Errorf("expected LKG host ai-container, got %s", lkgInstances[0].Host)
	}
}
