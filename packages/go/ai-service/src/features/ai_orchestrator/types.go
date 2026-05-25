package aiorchestrator

import (
	"context"
	"time"
)

type ModelInfo struct {
	ID          string `json:"id"`
	Name        string `json:"name"`
	Description string `json:"description"`
	Provider    string `json:"provider"`
}

type ChatMessage struct {
	Role      string    `json:"role"`
	Content   string    `json:"content"`
	Embedding []float32 `json:"-"`
	Timestamp int64     `json:"timestamp,omitempty"`
}

type UserFact struct {
	Fact       string    `json:"fact"`
	Importance int       `json:"importance"`
	Timestamp  int64     `json:"timestamp"`
	Embedding  []float32 `json:"-"`
}

type ChatSession struct {
	UserID         string        `json:"user_id"`
	Messages       []ChatMessage `json:"messages"`
	LastAccessedAt time.Time     `json:"last_accessed_at"`
	Facts          []UserFact    `json:"facts,omitempty"`
}

type CacheInfo struct {
	Cached    bool   `json:"cached"`
	CacheType string `json:"cache_type"`
}

type cacheInfoKey struct{}

func WithCacheInfo(ctx context.Context) (context.Context, *CacheInfo) {
	info := &CacheInfo{}
	return context.WithValue(ctx, cacheInfoKey{}, info), info
}

func GetCacheInfo(ctx context.Context) *CacheInfo {
	if info, ok := ctx.Value(cacheInfoKey{}).(*CacheInfo); ok {
		return info
	}
	return nil
}
