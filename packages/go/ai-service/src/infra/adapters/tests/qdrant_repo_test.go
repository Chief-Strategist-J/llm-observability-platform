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

func TestQdrantRepo_CreateCollection(t *testing.T) {
	calledGet := false
	calledPut := false

	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.Method == http.MethodGet && r.URL.Path == "/collections/my_collection" {
			calledGet = true
			w.WriteHeader(http.StatusNotFound)
			return
		}
		if r.Method == http.MethodPut && r.URL.Path == "/collections/my_collection" {
			calledPut = true
			w.WriteHeader(http.StatusOK)
			_, _ = w.Write([]byte(`{"status": "ok"}`))
			return
		}
		w.WriteHeader(http.StatusBadRequest)
	}))
	defer server.Close()

	repo := adapters.NewQdrantRepository(server.URL, "my-key", "my_collection")
	ctx := context.Background()

	err := repo.CreateCollectionIfNotExist(ctx, 384, "Cosine")
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

func TestQdrantRepo_Search(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.Method == http.MethodPost && r.URL.Path == "/collections/my_collection/points/search" {
			response := map[string]interface{}{
				"result": []map[string]interface{}{
					{
						"id":    "uuid-1",
						"score": 0.95,
						"payload": map[string]interface{}{
							"role":    "user",
							"content": "hello world",
							"user_id": "user-123",
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

	repo := adapters.NewQdrantRepository(server.URL, "my-key", "my_collection")
	ctx := context.Background()

	results, err := repo.Search(ctx, "user-123", []float32{0.1, 0.2}, 3)
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}

	if len(results) != 1 {
		t.Fatalf("expected 1 result, got %d", len(results))
	}
	if results[0].ID != "uuid-1" {
		t.Errorf("expected id uuid-1, got %s", results[0].ID)
	}
	if results[0].Payload["content"] != "hello world" {
		t.Errorf("unexpected content: %v", results[0].Payload["content"])
	}
}

func TestQdrantRepo_Upsert(t *testing.T) {
	calledPut := false
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.Method == http.MethodPut && r.URL.Path == "/collections/my_collection/points" {
			calledPut = true
			w.WriteHeader(http.StatusOK)
			_, _ = w.Write([]byte(`{"status": "ok"}`))
			return
		}
		w.WriteHeader(http.StatusBadRequest)
	}))
	defer server.Close()

	repo := adapters.NewQdrantRepository(server.URL, "my-key", "my_collection")
	ctx := context.Background()

	err := repo.Upsert(ctx, "uuid-123", []float32{0.1, 0.2}, map[string]interface{}{"role": "user"})
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}

	if !calledPut {
		t.Error("expected PUT /points to be called")
	}
}

func TestLiveQdrantIntegration(t *testing.T) {
	liveURL := os.Getenv("TEST_LIVE_QDRANT_URL")
	if liveURL == "" {
		t.Skip("TEST_LIVE_QDRANT_URL not set")
	}

	repo := adapters.NewQdrantRepository(liveURL, "", "test_collection_live")
	ctx := context.Background()

	err := repo.CreateCollectionIfNotExist(ctx, 4, "Cosine")
	if err != nil {
		t.Fatalf("failed to create collection: %v", err)
	}

	vector := []float32{0.1, 0.2, 0.3, 0.4}
	payload := map[string]interface{}{
		"user_id": "test-user-live",
		"role":    "user",
		"content": "hello live qdrant",
	}

	err = repo.Upsert(ctx, "00000000-0000-0000-0000-000000000001", vector, payload)
	if err != nil {
		t.Fatalf("failed to upsert point: %v", err)
	}

	results, err := repo.Search(ctx, "test-user-live", vector, 1)
	if err != nil {
		t.Fatalf("failed to search points: %v", err)
	}

	if len(results) == 0 {
		t.Fatal("expected at least 1 search result, got 0")
	}

	if results[0].ID != "00000000-0000-0000-0000-000000000001" {
		t.Errorf("expected ID 00000000-0000-0000-0000-000000000001, got %s", results[0].ID)
	}
}

