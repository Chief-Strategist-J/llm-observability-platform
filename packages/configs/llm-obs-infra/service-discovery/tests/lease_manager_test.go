package tests

import (
	"context"
	"testing"
	"time"

	"github.com/llm-observability/platform/packages/configs/llm-obs-infra/service-discovery/registry"
)

func TestLeaseManagerMarksUnhealthy(t *testing.T) {
	reg := registry.NewRegistry(registry.DefaultInstanceDefaults)
	inst := reg.Register(newTestInstance("lease-svc", "localhost", 8080))

	inst.LastHeartbeat = time.Now().Add(-2 * time.Second)

	config := registry.LeaseManagerConfig{
		SweepInterval: 50 * time.Millisecond,
		HeartbeatTTL:  1 * time.Second,
		EvictionTTL:   5 * time.Second,
	}
	lm := registry.NewLeaseManager(reg, config)

	ctx, cancel := context.WithCancel(context.Background())
	go lm.Start(ctx)

	time.Sleep(200 * time.Millisecond)
	cancel()

	got, ok := reg.GetInstance("lease-svc", inst.ID)
	if !ok {
		t.Fatal("instance should still exist (not yet evicted)")
	}
	if got.Status != registry.StatusUnhealthy {
		t.Fatalf("expected UNHEALTHY, got %s", got.Status)
	}
}

func TestLeaseManagerEvictsAfterGracePeriod(t *testing.T) {
	reg := registry.NewRegistry(registry.DefaultInstanceDefaults)
	inst := reg.Register(newTestInstance("lease-svc", "localhost", 8080))

	inst.LastHeartbeat = time.Now().Add(-10 * time.Second)

	config := registry.LeaseManagerConfig{
		SweepInterval: 50 * time.Millisecond,
		HeartbeatTTL:  100 * time.Millisecond,
		EvictionTTL:   200 * time.Millisecond,
	}
	lm := registry.NewLeaseManager(reg, config)

	ctx, cancel := context.WithCancel(context.Background())
	go lm.Start(ctx)

	time.Sleep(500 * time.Millisecond)
	cancel()

	all := reg.GetAll("lease-svc")
	if len(all) != 0 {
		t.Fatalf("expected 0 instances after eviction, got %d", len(all))
	}
}

func TestHeartbeatResetsUnhealthy(t *testing.T) {
	reg := registry.NewRegistry(registry.DefaultInstanceDefaults)
	inst := reg.Register(newTestInstance("lease-svc", "localhost", 8080))

	reg.UpdateStatus("lease-svc", inst.ID, registry.StatusUnhealthy, "heartbeat expired")

	err := reg.Heartbeat("lease-svc", inst.ID)
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}

	got, _ := reg.GetInstance("lease-svc", inst.ID)
	if got.Status != registry.StatusHealthy {
		t.Fatalf("expected HEALTHY after heartbeat, got %s", got.Status)
	}
}
