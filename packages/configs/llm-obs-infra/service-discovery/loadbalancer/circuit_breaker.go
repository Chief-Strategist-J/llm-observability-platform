package loadbalancer

import (
	"sync"
	"time"
)

type CircuitState int

const (
	CircuitClosed CircuitState = iota
	CircuitOpen
	CircuitHalfOpen
)

var circuitStateNames = map[CircuitState]string{
	CircuitClosed:   "CLOSED",
	CircuitOpen:     "OPEN",
	CircuitHalfOpen: "HALF_OPEN",
}

func (s CircuitState) String() string {
	if name, ok := circuitStateNames[s]; ok {
		return name
	}
	return "UNKNOWN"
}

type CircuitBreakerConfig struct {
	FailureThreshold int           `json:"failureThreshold"`
	CooldownDuration time.Duration `json:"cooldownDuration"`
	HalfOpenMaxCalls int           `json:"halfOpenMaxCalls"`
}

var DefaultCircuitBreakerConfig = CircuitBreakerConfig{
	FailureThreshold: 5,
	CooldownDuration: 30 * time.Second,
	HalfOpenMaxCalls: 1,
}

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
