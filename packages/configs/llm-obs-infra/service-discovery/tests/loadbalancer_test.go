package tests

import (
	"testing"

	"github.com/llm-observability/platform/packages/configs/llm-obs-infra/service-discovery/loadbalancer"
	"github.com/llm-observability/platform/packages/configs/llm-obs-infra/service-discovery/registry"
)

func TestLoadBalancingAlgorithms(t *testing.T) {
	inst1 := &registry.ServiceInstance{ID: "inst-1", Name: "svc", Host: "10.0.0.1", Port: 8080, Weight: 100}
	inst2 := &registry.ServiceInstance{ID: "inst-2", Name: "svc", Host: "10.0.0.2", Port: 8080, Weight: 200}
	instances := []*registry.ServiceInstance{inst1, inst2}

	// 1. Round Robin
	rr, err := loadbalancer.NewBalancer(loadbalancer.AlgorithmRoundRobin)
	if err != nil {
		t.Fatalf("failed to create round_robin balancer: %v", err)
	}
	picked1, _ := rr.Pick(instances, "")
	picked2, _ := rr.Pick(instances, "")
	if picked1.ID == picked2.ID {
		t.Errorf("expected different instances on consecutive round_robin picks")
	}

	// 2. Weighted Round Robin
	wrr, err := loadbalancer.NewBalancer(loadbalancer.AlgorithmWeightedRR)
	if err != nil {
		t.Fatalf("failed to create weighted_round_robin balancer: %v", err)
	}
	picks := make(map[string]int)
	for i := 0; i < 300; i++ {
		p, _ := wrr.Pick(instances, "")
		picks[p.ID]++
	}
	if picks["inst-2"] <= picks["inst-1"] {
		t.Errorf("expected inst-2 (weight 200) to receive more picks than inst-1 (weight 100), got %v", picks)
	}

	// 3. Least Connections
	lc, err := loadbalancer.NewBalancer(loadbalancer.AlgorithmLeastConn)
	if err != nil {
		t.Fatalf("failed to create least_connections balancer: %v", err)
	}
	pLeast, _ := lc.Pick(instances, "")
	if pLeast == nil {
		t.Fatalf("least_connections pick returned nil")
	}

	// 4. Power of Two Choices
	p2c, err := loadbalancer.NewBalancer(loadbalancer.AlgorithmP2C)
	if err != nil {
		t.Fatalf("failed to create p2c balancer: %v", err)
	}
	pP2C, _ := p2c.Pick(instances, "")
	if pP2C == nil {
		t.Fatalf("p2c pick returned nil")
	}

	// 5. Consistent Hashing
	ch, err := loadbalancer.NewBalancer(loadbalancer.AlgorithmConsistentHash)
	if err != nil {
		t.Fatalf("failed to create consistent_hash balancer: %v", err)
	}
	keyPick1, _ := ch.Pick(instances, "user-session-12345")
	keyPick2, _ := ch.Pick(instances, "user-session-12345")
	if keyPick1.ID != keyPick2.ID {
		t.Errorf("expected consistent_hash to pick same instance for identical key, got %s and %s", keyPick1.ID, keyPick2.ID)
	}
}

func TestCircuitBreakerStateTransitions(t *testing.T) {
	config := loadbalancer.DefaultCircuitBreakerConfig
	config.FailureThreshold = 2
	cb := loadbalancer.NewCircuitBreaker(config)

	if cb.State() != loadbalancer.CircuitClosed {
		t.Fatalf("expected initial state CLOSED, got %s", cb.State())
	}

	cb.RecordFailure()
	if cb.State() != loadbalancer.CircuitClosed {
		t.Fatalf("expected state CLOSED after 1 failure, got %s", cb.State())
	}

	cb.RecordFailure() // Trips to OPEN
	if cb.State() != loadbalancer.CircuitOpen {
		t.Fatalf("expected state OPEN after 2 failures, got %s", cb.State())
	}

	if cb.AllowRequest() {
		t.Errorf("expected AllowRequest to return false when CircuitBreaker is OPEN")
	}

	cb.RecordSuccess()
	if cb.State() != loadbalancer.CircuitClosed {
		t.Fatalf("expected state CLOSED after RecordSuccess, got %s", cb.State())
	}
}
