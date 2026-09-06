package tests

import (
	"context"
	"testing"
	"time"

	"github.com/llm-observability/platform/packages/configs/llm-obs-infra/service-discovery/registry"
)

func TestLeaseManagerSweepAndEviction(t *testing.T) {
	reg := registry.NewRegistry(registry.DefaultInstanceDefaults)

	inst := &registry.ServiceInstance{
		Name:     "ttl-svc",
		Host:     "localhost",
		Port:     8080,
		Protocol: "http",
	}
	registered := reg.Register(inst)

	// Short TTL config for quick testing
	cfg := registry.LeaseManagerConfig{
		SweepInterval: 50 * time.Millisecond,
		HeartbeatTTL:  100 * time.Millisecond,
		EvictionTTL:   250 * time.Millisecond,
	}

	lm := registry.NewLeaseManager(reg, cfg)

	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()

	go lm.Start(ctx)

	// 1. Initially healthy
	healthy := reg.GetHealthy("ttl-svc")
	if len(healthy) == 0 {
		t.Fatalf("expected 1 healthy instance initially")
	}

	// 2. Wait for HeartbeatTTL to expire -> status should change to UNHEALTHY
	time.Sleep(150 * time.Millisecond)
	healthyAfterTTL := reg.GetHealthy("ttl-svc")
	if len(healthyAfterTTL) != 0 {
		t.Errorf("expected 0 healthy instances after HeartbeatTTL expired")
	}

	allInstances := reg.GetAll("ttl-svc")
	if len(allInstances) == 0 || allInstances[0].Status != registry.StatusUnhealthy {
		t.Errorf("expected instance status UNHEALTHY after HeartbeatTTL expired")
	}

	// 3. Wait for EvictionTTL -> instance should be evicted completely
	time.Sleep(200 * time.Millisecond)
	evictedInstances := reg.GetAll("ttl-svc")
	if len(evictedInstances) != 0 {
		t.Errorf("expected instance to be evicted completely after EvictionTTL, found %d", len(evictedInstances))
	}
	_ = registered
}
