package tests

import (
	"fmt"
	"testing"

	"github.com/llm-observability/platform/packages/configs/llm-obs-infra/service-discovery/loadbalancer"
	"github.com/llm-observability/platform/packages/configs/llm-obs-infra/service-discovery/registry"
)

func makeInstances(count int) []*registry.ServiceInstance {
	instances := make([]*registry.ServiceInstance, count)
	for i := 0; i < count; i++ {
		instances[i] = &registry.ServiceInstance{
			ID:       fmt.Sprintf("inst-%d", i),
			Name:     "test-svc",
			Host:     "localhost",
			Port:     8080 + i,
			Protocol: "http",
			Weight:   100,
		}
	}
	return instances
}

func TestRoundRobinDistribution(t *testing.T) {
	balancer, _ := loadbalancer.NewBalancer(loadbalancer.AlgorithmRoundRobin)
	instances := makeInstances(3)

	hits := make(map[string]int)
	for i := 0; i < 9; i++ {
		inst, err := balancer.Pick(instances, "")
		if err != nil {
			t.Fatalf("unexpected error: %v", err)
		}
		hits[inst.ID]++
	}

	for _, inst := range instances {
		if hits[inst.ID] != 3 {
			t.Fatalf("expected 3 hits for %s, got %d", inst.ID, hits[inst.ID])
		}
	}
}

func TestWeightedRoundRobinDistribution(t *testing.T) {
	balancer, _ := loadbalancer.NewBalancer(loadbalancer.AlgorithmWeightedRR)
	instances := []*registry.ServiceInstance{
		{ID: "heavy", Name: "test-svc", Host: "localhost", Port: 8080, Protocol: "http", Weight: 300},
		{ID: "light", Name: "test-svc", Host: "localhost", Port: 8081, Protocol: "http", Weight: 100},
	}

	hits := make(map[string]int)
	for i := 0; i < 400; i++ {
		inst, _ := balancer.Pick(instances, "")
		hits[inst.ID]++
	}

	if hits["heavy"] <= hits["light"] {
		t.Fatalf("heavy (%d) should have more hits than light (%d)", hits["heavy"], hits["light"])
	}
}

func TestLeastConnections(t *testing.T) {
	balancer, _ := loadbalancer.NewBalancer(loadbalancer.AlgorithmLeastConn)
	instances := makeInstances(3)

	inst, err := balancer.Pick(instances, "")
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if inst == nil {
		t.Fatal("expected non-nil instance")
	}
}

func TestPowerOfTwoChoices(t *testing.T) {
	balancer, _ := loadbalancer.NewBalancer(loadbalancer.AlgorithmP2C)
	instances := makeInstances(5)

	inst, err := balancer.Pick(instances, "")
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if inst == nil {
		t.Fatal("expected non-nil instance")
	}
}

func TestConsistentHashStickiness(t *testing.T) {
	balancer, _ := loadbalancer.NewBalancer(loadbalancer.AlgorithmConsistentHash)
	instances := makeInstances(5)

	first, _ := balancer.Pick(instances, "session-123")
	for i := 0; i < 10; i++ {
		got, _ := balancer.Pick(instances, "session-123")
		if got.ID != first.ID {
			t.Fatalf("expected consistent pick %s, got %s", first.ID, got.ID)
		}
	}
}

func TestPickFromEmptyInstances(t *testing.T) {
	algorithms := []loadbalancer.Algorithm{
		loadbalancer.AlgorithmRoundRobin,
		loadbalancer.AlgorithmWeightedRR,
		loadbalancer.AlgorithmLeastConn,
		loadbalancer.AlgorithmP2C,
		loadbalancer.AlgorithmConsistentHash,
	}

	for _, algo := range algorithms {
		balancer, _ := loadbalancer.NewBalancer(algo)
		_, err := balancer.Pick(nil, "")
		if err == nil {
			t.Fatalf("expected error for empty instances with algorithm %s", algo)
		}
	}
}

func TestNewBalancerUnknownAlgorithm(t *testing.T) {
	_, err := loadbalancer.NewBalancer("unknown_algorithm")
	if err == nil {
		t.Fatal("expected error for unknown algorithm")
	}
}
