package tests

import (
	"context"
	"testing"
	"time"

	"github.com/llm-observability/platform/packages/go/ai-service/src/infra/adapters"
)

func TestMemoryCacheCRUD(t *testing.T) {
	cache := adapters.NewMemoryResponseCache(10*time.Minute, 1*time.Minute)
	defer cache.Stop()

	ctx := context.Background()
	val, err := cache.Get(ctx, "key-1")
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if val != "" {
		t.Errorf("expected empty string, got %v", val)
	}

	err = cache.Set(ctx, "key-1", "value-1")
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}

	val, err = cache.Get(ctx, "key-1")
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if val != "value-1" {
		t.Errorf("expected value-1, got %v", val)
	}
}

func TestMemoryCacheTTL(t *testing.T) {
	cache := adapters.NewMemoryResponseCache(10*time.Millisecond, 5*time.Millisecond)
	defer cache.Stop()

	ctx := context.Background()
	err := cache.Set(ctx, "key-2", "value-2")
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}

	time.Sleep(30 * time.Millisecond)

	val, err := cache.Get(ctx, "key-2")
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if val != "" {
		t.Errorf("expected value to be expired, got %v", val)
	}
}
