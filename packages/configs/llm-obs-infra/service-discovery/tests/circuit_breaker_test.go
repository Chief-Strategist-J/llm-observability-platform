package tests

import (
	"testing"
	"time"

	"github.com/llm-observability/platform/packages/configs/llm-obs-infra/service-discovery/loadbalancer"
)

func TestCircuitBreakerStartsClosed(t *testing.T) {
	cb := loadbalancer.NewCircuitBreaker(loadbalancer.DefaultCircuitBreakerConfig)

	if cb.State() != loadbalancer.CircuitClosed {
		t.Fatalf("expected CLOSED, got %s", cb.State())
	}
	if !cb.AllowRequest() {
		t.Fatal("expected request to be allowed in CLOSED state")
	}
}

func TestCircuitBreakerOpensAfterThreshold(t *testing.T) {
	config := loadbalancer.CircuitBreakerConfig{
		FailureThreshold: 3,
		CooldownDuration: 1 * time.Second,
		HalfOpenMaxCalls: 1,
	}
	cb := loadbalancer.NewCircuitBreaker(config)

	for i := 0; i < 3; i++ {
		cb.RecordFailure()
	}

	if cb.State() != loadbalancer.CircuitOpen {
		t.Fatalf("expected OPEN after %d failures, got %s", 3, cb.State())
	}
	if cb.AllowRequest() {
		t.Fatal("expected request to be blocked in OPEN state")
	}
}

func TestCircuitBreakerTransitionsToHalfOpen(t *testing.T) {
	config := loadbalancer.CircuitBreakerConfig{
		FailureThreshold: 2,
		CooldownDuration: 50 * time.Millisecond,
		HalfOpenMaxCalls: 1,
	}
	cb := loadbalancer.NewCircuitBreaker(config)

	cb.RecordFailure()
	cb.RecordFailure()

	time.Sleep(100 * time.Millisecond)

	if !cb.AllowRequest() {
		t.Fatal("expected request to be allowed in HALF_OPEN state")
	}
	if cb.State() != loadbalancer.CircuitHalfOpen {
		t.Fatalf("expected HALF_OPEN, got %s", cb.State())
	}
}

func TestCircuitBreakerClosesOnSuccess(t *testing.T) {
	config := loadbalancer.CircuitBreakerConfig{
		FailureThreshold: 2,
		CooldownDuration: 50 * time.Millisecond,
		HalfOpenMaxCalls: 1,
	}
	cb := loadbalancer.NewCircuitBreaker(config)

	cb.RecordFailure()
	cb.RecordFailure()

	time.Sleep(100 * time.Millisecond)
	cb.AllowRequest()
	cb.RecordSuccess()

	if cb.State() != loadbalancer.CircuitClosed {
		t.Fatalf("expected CLOSED after success, got %s", cb.State())
	}
}

func TestCircuitBreakerReopensOnHalfOpenFailure(t *testing.T) {
	config := loadbalancer.CircuitBreakerConfig{
		FailureThreshold: 2,
		CooldownDuration: 50 * time.Millisecond,
		HalfOpenMaxCalls: 1,
	}
	cb := loadbalancer.NewCircuitBreaker(config)

	cb.RecordFailure()
	cb.RecordFailure()

	time.Sleep(100 * time.Millisecond)
	cb.AllowRequest()
	cb.RecordFailure()

	if cb.State() != loadbalancer.CircuitOpen {
		t.Fatalf("expected OPEN after half-open failure, got %s", cb.State())
	}
}

func TestCircuitBreakerRegistryCreateOnDemand(t *testing.T) {
	cbReg := loadbalancer.NewCircuitBreakerRegistry(loadbalancer.DefaultCircuitBreakerConfig)

	cb1 := cbReg.Get("instance-1")
	cb2 := cbReg.Get("instance-1")

	if cb1 != cb2 {
		t.Fatal("expected same circuit breaker instance for same ID")
	}

	cb3 := cbReg.Get("instance-2")
	if cb1 == cb3 {
		t.Fatal("expected different circuit breaker for different ID")
	}
}
