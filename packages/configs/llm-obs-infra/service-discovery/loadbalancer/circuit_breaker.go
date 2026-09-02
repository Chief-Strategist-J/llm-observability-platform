package loadbalancer

import (
	"sync"
	"time"

	"github.com/llm-observability/platform/packages/configs/llm-obs-infra/service-discovery/models"
)

type CircuitState = models.CircuitState

const (
	CircuitClosed   = models.CircuitClosed
	CircuitOpen     = models.CircuitOpen
	CircuitHalfOpen = models.CircuitHalfOpen
)

type CircuitBreakerConfig = models.CircuitBreakerConfig

var DefaultCircuitBreakerConfig = models.DefaultCircuitBreakerConfig

type CircuitBreaker struct {
	mu               sync.Mutex
	config           CircuitBreakerConfig
	state            CircuitState
	consecutiveFails int
	lastFailTime     time.Time
	halfOpenCalls    int
}

func NewCircuitBreaker(config CircuitBreakerConfig) *CircuitBreaker {
	return &CircuitBreaker{config: config, state: CircuitClosed}
}

func (cb *CircuitBreaker) AllowRequest() bool {
	cb.mu.Lock()
	defer cb.mu.Unlock()

	switch cb.state {
	case CircuitClosed:
		return true
	case CircuitOpen:
		if time.Since(cb.lastFailTime) > cb.config.CooldownDuration {
			cb.state = CircuitHalfOpen
			cb.halfOpenCalls = 0
			return true
		}
		return false
	case CircuitHalfOpen:
		if cb.halfOpenCalls < cb.config.HalfOpenMaxCalls {
			cb.halfOpenCalls++
			return true
		}
		return false
	}
	return false
}

func (cb *CircuitBreaker) RecordSuccess() {
	cb.mu.Lock()
	defer cb.mu.Unlock()

	cb.consecutiveFails = 0
	cb.state = CircuitClosed
}

func (cb *CircuitBreaker) RecordFailure() {
	cb.mu.Lock()
	defer cb.mu.Unlock()

	cb.consecutiveFails++
	cb.lastFailTime = time.Now()

	if cb.consecutiveFails >= cb.config.FailureThreshold || cb.state == CircuitHalfOpen {
		cb.state = CircuitOpen
	}
}

func (cb *CircuitBreaker) State() CircuitState {
	cb.mu.Lock()
	defer cb.mu.Unlock()
	return cb.state
}

type CircuitBreakerRegistry struct {
	mu       sync.RWMutex
	breakers map[string]*CircuitBreaker
	config   CircuitBreakerConfig
}

func NewCircuitBreakerRegistry(config CircuitBreakerConfig) *CircuitBreakerRegistry {
	return &CircuitBreakerRegistry{
		breakers: make(map[string]*CircuitBreaker),
		config:   config,
	}
}

func (cbr *CircuitBreakerRegistry) Get(instanceID string) *CircuitBreaker {
	cbr.mu.RLock()
	cb, ok := cbr.breakers[instanceID]
	cbr.mu.RUnlock()

	if ok {
		return cb
	}

	cbr.mu.Lock()
	defer cbr.mu.Unlock()

	cb, ok = cbr.breakers[instanceID]
	if ok {
		return cb
	}

	cb = NewCircuitBreaker(cbr.config)
	cbr.breakers[instanceID] = cb
	return cb
}
