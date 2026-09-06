package adapters

import (
	"context"
	"os"
	"strings"
	"sync"
	"time"
)

type cacheEntry struct {
	value     string
	createdAt time.Time
}

type MemoryResponseCache struct {
	mu       sync.RWMutex
	entries  map[string]cacheEntry
	ttl      time.Duration
	stopChan chan struct{}
}

func NewMemoryResponseCache(ttl time.Duration, cleanupInterval time.Duration) *MemoryResponseCache {
	c := &MemoryResponseCache{
		entries:  make(map[string]cacheEntry),
		ttl:      ttl,
		stopChan: make(chan struct{}),
	}
	go c.startCleanupLoop(cleanupInterval)
	return c
}

func (c *MemoryResponseCache) Stop() {
	close(c.stopChan)
}

func (c *MemoryResponseCache) Get(ctx context.Context, key string) (string, error) {
	c.mu.RLock()
	defer c.mu.RUnlock()

	entry, exists := c.entries[key]
	if !exists {
		return "", nil
	}

	ttl := c.ttl
	if strings.HasPrefix(key, "stateless:") {
		if valStr := os.Getenv("AI_STATELESS_TTL"); valStr != "" {
			if d, err := time.ParseDuration(valStr); err == nil {
				ttl = d
			}
		} else {
			ttl = 24 * time.Hour
		}
	} else if strings.HasPrefix(key, "stateful:") {
		if valStr := os.Getenv("AI_STATEFUL_TTL"); valStr != "" {
			if d, err := time.ParseDuration(valStr); err == nil {
				ttl = d
			}
		} else {
			ttl = 1 * time.Hour
		}
	}

	if time.Since(entry.createdAt) > ttl {
		return "", nil
	}

	return entry.value, nil
}

func (c *MemoryResponseCache) Set(ctx context.Context, key string, value string) error {
	c.mu.Lock()
	defer c.mu.Unlock()

	c.entries[key] = cacheEntry{
		value:     value,
		createdAt: time.Now(),
	}
	return nil
}

func (c *MemoryResponseCache) startCleanupLoop(interval time.Duration) {
	ticker := time.NewTicker(interval)
	defer ticker.Stop()

	for {
		select {
		case <-ticker.C:
			c.mu.Lock()
			now := time.Now()
			for k, entry := range c.entries {
				ttl := c.ttl
				if strings.HasPrefix(k, "stateless:") {
					if valStr := os.Getenv("AI_STATELESS_TTL"); valStr != "" {
						if d, err := time.ParseDuration(valStr); err == nil {
							ttl = d
						}
					} else {
						ttl = 24 * time.Hour
					}
				} else if strings.HasPrefix(k, "stateful:") {
					if valStr := os.Getenv("AI_STATEFUL_TTL"); valStr != "" {
						if d, err := time.ParseDuration(valStr); err == nil {
							ttl = d
						}
					} else {
						ttl = 1 * time.Hour
					}
				}
				if now.Sub(entry.createdAt) > ttl {
					delete(c.entries, k)
				}
			}
			c.mu.Unlock()
		case <-c.stopChan:
			return
		}
	}
}
