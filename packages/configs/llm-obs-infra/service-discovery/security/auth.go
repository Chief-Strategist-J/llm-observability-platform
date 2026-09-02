package security

import (
	"net/http"
	"strings"
	"sync"
	"time"
)

type TokenBucketLimiter struct {
	rate       int
	capacity   int
	tokens     map[string]int
	lastRefill map[string]time.Time
	mu         sync.Mutex
}

func NewTokenBucketLimiter(rate, capacity int) *TokenBucketLimiter {
	if rate <= 0 {
		rate = 100
	}
	if capacity <= 0 {
		capacity = rate * 2
	}
	return &TokenBucketLimiter{
		rate:       rate,
		capacity:   capacity,
		tokens:     make(map[string]int),
		lastRefill: make(map[string]time.Time),
	}
}

func (l *TokenBucketLimiter) Allow(key string) bool {
	l.mu.Lock()
	defer l.mu.Unlock()

	now := time.Now()
	last, exists := l.lastRefill[key]
	if !exists {
		l.tokens[key] = l.capacity - 1
		l.lastRefill[key] = now
		return true
	}

	elapsed := now.Sub(last).Seconds()
	l.lastRefill[key] = now
	l.tokens[key] += int(elapsed * float64(l.rate))
	if l.tokens[key] > l.capacity {
		l.tokens[key] = l.capacity
	}

	if l.tokens[key] > 0 {
		l.tokens[key]--
		return true
	}

	return false
}

func ValidateBearerAuth(req *http.Request, expectedToken string) bool {
	if expectedToken == "" {
		return true // Open mode if token is not configured
	}

	authHeader := req.Header.Get("Authorization")
	if authHeader == "" {
		return false
	}

	parts := strings.SplitN(authHeader, " ", 2)
	if len(parts) != 2 || !strings.EqualFold(parts[0], "Bearer") {
		return false
	}

	return parts[1] == expectedToken
}
