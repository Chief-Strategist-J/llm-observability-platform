package adapters

import (
	"context"
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

	if time.Since(entry.createdAt) > c.ttl {
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
				if now.Sub(entry.createdAt) > c.ttl {
					delete(c.entries, k)
				}
			}
			c.mu.Unlock()
		case <-c.stopChan:
			return
		}
	}
}
