package tests

import (
	"context"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"os"
	"testing"

	"github.com/llm-observability/platform/packages/go/ai-service/src/infra/adapters"
)

func TestQdrantSemanticCache_CreateCollection(t *testing.T) {
	calledGet := false
	calledPut := false

	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.Method == http.MethodGet && r.URL.Path == "/collections/semantic_cache" {
			calledGet = true
			w.WriteHeader(http.StatusNotFound)
			return
		}
		if r.Method == http.MethodPut && r.URL.Path == "/collections/semantic_cache" {
			calledPut = true
			w.WriteHeader(http.StatusOK)
			_, _ = w.Write([]byte(`{"status": "ok"}`))
			return
		}
		w.WriteHeader(http.StatusBadRequest)
	}))
	defer server.Close()

	cache := adapters.NewQdrantSemanticCache(server.URL, "my-key", "semantic_cache")
	ctx := context.Background()

	err := cache.CreateCollectionIfNotExist(ctx, 384, "Cosine")
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}

	if !calledGet {
		t.Error("expected GET collection to be called")
	}
	if !calledPut {
		t.Error("expected PUT collection to be called")
	}
}

func TestQdrantSemanticCache_GetSimilar(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.Method == http.MethodPost && r.URL.Path == "/collections/semantic_cache/points/search" {
			var body map[string]interface{}
			_ = json.NewDecoder(r.Body).Decode(&body)
			if threshold, ok := body["score_threshold"].(float64); !ok || threshold != 0.92 {
				w.WriteHeader(http.StatusBadRequest)
				return
			}
			response := map[string]interface{}{
				"result": []map[string]interface{}{
					{
						"id":    "uuid-1",
						"score": 0.95,
						"payload": map[string]interface{}{
							"prompt":   "hello",
							"response": "hi there",
						},
					},
				},
				"status": "ok",
			}
			w.WriteHeader(http.StatusOK)
			_ = json.NewEncoder(w).Encode(response)
			return
		}
		w.WriteHeader(http.StatusBadRequest)
	}))
	defer server.Close()

	cache := adapters.NewQdrantSemanticCache(server.URL, "my-key", "semantic_cache")
	ctx := context.Background()

	val, err := cache.GetSimilar(ctx, []float32{0.1, 0.2}, 0.92)
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if val != "hi there" {
		t.Errorf("expected hi there, got %s", val)
	}
}

func TestQdrantSemanticCache_Save(t *testing.T) {
	calledPut := false
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.Method == http.MethodPut && r.URL.Path == "/collections/semantic_cache/points" {
			calledPut = true
			w.WriteHeader(http.StatusOK)
			_, _ = w.Write([]byte(`{"status": "ok"}`))
			return
		}
		w.WriteHeader(http.StatusBadRequest)
	}))
	defer server.Close()

	cache := adapters.NewQdrantSemanticCache(server.URL, "my-key", "semantic_cache")
	ctx := context.Background()

	err := cache.Save(ctx, []float32{0.1, 0.2}, "hello", "hi there")
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}

	if !calledPut {
		t.Error("expected PUT /points to be called")
	}
}

func TestLiveQdrantSemanticCacheIntegration(t *testing.T) {
	liveURL := os.Getenv("TEST_LIVE_QDRANT_URL")
	if liveURL == "" {
		t.Skip("TEST_LIVE_QDRANT_URL not set")
	}

	cache := adapters.NewQdrantSemanticCache(liveURL, "", "test_semantic_cache_live")
	ctx := context.Background()

	err := cache.CreateCollectionIfNotExist(ctx, 4, "Cosine")
	if err != nil {
		t.Fatalf("failed to create collection: %v", err)
	}

	vector := []float32{0.1, 0.2, 0.3, 0.4}
	err = cache.Save(ctx, vector, "hello live", "hi live response")
	if err != nil {
		t.Fatalf("failed to save cache entry: %v", err)
	}

	val, err := cache.GetSimilar(ctx, vector, 0.9)
	if err != nil {
		t.Fatalf("failed to get similar entry: %v", err)
	}
	if val != "hi live response" {
		t.Errorf("expected hi live response, got %s", val)
	}
}
