package adapters

import (
	"bytes"
	"context"
	"crypto/rand"
	"encoding/json"
	"fmt"
	"net/http"
	"strings"
	"time"

	aiorchestrator "github.com/llm-observability/platform/packages/go/ai-service/src/features/ai_orchestrator"
)

type QdrantRepository struct {
	url        string
	apiKey     string
	collection string
	client     *http.Client
}

func NewQdrantRepository(url, apiKey, collection string) *QdrantRepository {
	if collection == "" {
		collection = "chat_messages"
	}
	return &QdrantRepository{
		url:        strings.TrimSuffix(url, "/"),
		apiKey:     apiKey,
		collection: collection,
		client: &http.Client{
			Timeout: 10 * time.Second,
		},
	}
}

func (r *QdrantRepository) addHeaders(req *http.Request) {
	req.Header.Set("Content-Type", "application/json")
	if r.apiKey != "" {
		req.Header.Set("api-key", r.apiKey)
	}
}

func (r *QdrantRepository) CreateCollectionIfNotExist(ctx context.Context, vectorSize int, distance string) error {
	url := fmt.Sprintf("%s/collections/%s", r.url, r.collection)
	req, err := http.NewRequestWithContext(ctx, http.MethodGet, url, nil)
	if err != nil {
		return err
	}
	r.addHeaders(req)

	resp, err := r.client.Do(req)
	if err != nil {
		return err
	}
	defer resp.Body.Close()

	if resp.StatusCode == http.StatusOK {
		return nil
	}

	if resp.StatusCode == http.StatusNotFound {
		createURL := fmt.Sprintf("%s/collections/%s", r.url, r.collection)
		body := map[string]interface{}{
			"vectors": map[string]interface{}{
				"size":     vectorSize,
				"distance": distance,
			},
		}
		bodyBytes, err := json.Marshal(body)
		if err != nil {
			return err
		}

		createReq, err := http.NewRequestWithContext(ctx, http.MethodPut, createURL, bytes.NewBuffer(bodyBytes))
		if err != nil {
			return err
		}
		r.addHeaders(createReq)

		createResp, err := r.client.Do(createReq)
		if err != nil {
			return err
		}
		defer createResp.Body.Close()

		if createResp.StatusCode != http.StatusOK {
			return fmt.Errorf("failed to create collection: status %d", createResp.StatusCode)
		}
		return nil
	}

	return fmt.Errorf("unexpected status code checking collection: %d", resp.StatusCode)
}

func (r *QdrantRepository) Search(ctx context.Context, userID string, vector []float32, limit int) ([]aiorchestrator.SearchResult, error) {
	url := fmt.Sprintf("%s/collections/%s/points/search", r.url, r.collection)
	body := map[string]interface{}{
		"vector":       vector,
		"limit":        limit,
		"with_payload": true,
		"filter": map[string]interface{}{
			"must": []map[string]interface{}{
				{
					"key": "user_id",
					"match": map[string]interface{}{
						"value": userID,
					},
				},
			},
		},
	}
	bodyBytes, err := json.Marshal(body)
	if err != nil {
		return nil, err
	}

	req, err := http.NewRequestWithContext(ctx, http.MethodPost, url, bytes.NewBuffer(bodyBytes))
	if err != nil {
		return nil, err
	}
	r.addHeaders(req)

	resp, err := r.client.Do(req)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("search failed with status code: %d", resp.StatusCode)
	}

	var searchResp struct {
		Result []struct {
			ID      string                 `json:"id"`
			Score   float32                `json:"score"`
			Payload map[string]interface{} `json:"payload"`
		} `json:"result"`
	}

	if err := json.NewDecoder(resp.Body).Decode(&searchResp); err != nil {
		return nil, err
	}

	var results []aiorchestrator.SearchResult
	for _, res := range searchResp.Result {
		results = append(results, aiorchestrator.SearchResult{
			ID:      res.ID,
			Score:   res.Score,
			Payload: res.Payload,
		})
	}
	return results, nil
}

func (r *QdrantRepository) Upsert(ctx context.Context, id string, vector []float32, payload map[string]interface{}) error {
	url := fmt.Sprintf("%s/collections/%s/points?wait=true", r.url, r.collection)
	body := map[string]interface{}{
		"points": []map[string]interface{}{
			{
				"id":      id,
				"vector":  vector,
				"payload": payload,
			},
		},
	}
	bodyBytes, err := json.Marshal(body)
	if err != nil {
		return err
	}

	req, err := http.NewRequestWithContext(ctx, http.MethodPut, url, bytes.NewBuffer(bodyBytes))
	if err != nil {
		return err
	}
	r.addHeaders(req)

	resp, err := r.client.Do(req)
	if err != nil {
		return err
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return fmt.Errorf("upsert failed with status code: %d", resp.StatusCode)
	}
	return nil
}

func GenerateUUID() string {
	b := make([]byte, 16)
	_, _ = rand.Read(b)
	b[6] = (b[6] & 0x0f) | 0x40
	b[8] = (b[8] & 0x3f) | 0x80
	return fmt.Sprintf("%x-%x-%x-%x-%x", b[0:4], b[4:6], b[6:8], b[8:10], b[10:])
}
