package adapters

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"net/http"
	"os"
	"strings"
	"time"

	"go.opentelemetry.io/otel"
	"go.opentelemetry.io/otel/codes"
)

type QdrantSemanticCache struct {
	url        string
	apiKey     string
	collection string
	client     *http.Client
}

func NewQdrantSemanticCache(url, apiKey, collection string) *QdrantSemanticCache {
	if collection == "" {
		collection = "semantic_cache"
	}
	return &QdrantSemanticCache{
		url:        strings.TrimSuffix(url, "/"),
		apiKey:     apiKey,
		collection: collection,
		client: &http.Client{
			Timeout: 10 * time.Second,
		},
	}
}

func (c *QdrantSemanticCache) addHeaders(req *http.Request) {
	req.Header.Set("Content-Type", "application/json")
	if c.apiKey != "" {
		req.Header.Set("api-key", c.apiKey)
	}
}

func (c *QdrantSemanticCache) CreateCollectionIfNotExist(ctx context.Context, vectorSize int, distance string) error {
	url := fmt.Sprintf("%s/collections/%s", c.url, c.collection)
	req, err := http.NewRequestWithContext(ctx, http.MethodGet, url, nil)
	if err != nil {
		return err
	}
	c.addHeaders(req)

	resp, err := c.client.Do(req)
	if err != nil {
		return err
	}
	defer resp.Body.Close()

	if resp.StatusCode == http.StatusOK {
		return nil
	}

	if resp.StatusCode == http.StatusNotFound {
		createURL := fmt.Sprintf("%s/collections/%s", c.url, c.collection)
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
		c.addHeaders(createReq)

		createResp, err := c.client.Do(createReq)
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

func (c *QdrantSemanticCache) GetSimilar(ctx context.Context, vector []float32, threshold float32, fingerprint string) (string, error) {
	tracer := otel.Tracer("qdrant-cache")
	ctx, span := tracer.Start(ctx, "QdrantSemanticCache.GetSimilar")
	defer span.End()

	ttl := 24 * time.Hour
	if strings.HasPrefix(fingerprint, "stateless:") {
		if valStr := os.Getenv("AI_STATELESS_TTL"); valStr != "" {
			if d, err := time.ParseDuration(valStr); err == nil {
				ttl = d
			}
		} else {
			ttl = 24 * time.Hour
		}
	} else if strings.HasPrefix(fingerprint, "stateful:") {
		if valStr := os.Getenv("AI_STATEFUL_TTL"); valStr != "" {
			if d, err := time.ParseDuration(valStr); err == nil {
				ttl = d
			}
		} else {
			ttl = 1 * time.Hour
		}
	}
	minTimestamp := time.Now().Add(-ttl).Unix()

	url := fmt.Sprintf("%s/collections/%s/points/search", c.url, c.collection)
	body := map[string]interface{}{
		"vector":          vector,
		"limit":           1,
		"with_payload":    true,
		"score_threshold": threshold,
		"filter": map[string]interface{}{
			"must": []map[string]interface{}{
				{
					"key": "fingerprint",
					"match": map[string]interface{}{
						"value": fingerprint,
					},
				},
				{
					"key": "timestamp",
					"range": map[string]interface{}{
						"gte": minTimestamp,
					},
				},
			},
		},
	}
	bodyBytes, err := json.Marshal(body)
	if err != nil {
		span.RecordError(err)
		span.SetStatus(codes.Error, err.Error())
		return "", err
	}

	req, err := http.NewRequestWithContext(ctx, http.MethodPost, url, bytes.NewBuffer(bodyBytes))
	if err != nil {
		span.RecordError(err)
		span.SetStatus(codes.Error, err.Error())
		return "", err
	}
	c.addHeaders(req)

	resp, err := c.client.Do(req)
	if err != nil {
		span.RecordError(err)
		span.SetStatus(codes.Error, err.Error())
		return "", err
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		err := fmt.Errorf("search failed with status code: %d", resp.StatusCode)
		span.RecordError(err)
		span.SetStatus(codes.Error, err.Error())
		return "", err
	}

	var searchResp struct {
		Result []struct {
			ID      string                 `json:"id"`
			Score   float32                `json:"score"`
			Payload map[string]interface{} `json:"payload"`
		} `json:"result"`
	}

	if err := json.NewDecoder(resp.Body).Decode(&searchResp); err != nil {
		span.RecordError(err)
		span.SetStatus(codes.Error, err.Error())
		return "", err
	}

	if len(searchResp.Result) > 0 {
		if respVal, ok := searchResp.Result[0].Payload["response"].(string); ok {
			return respVal, nil
		}
	}

	return "", nil
}

func (c *QdrantSemanticCache) Save(ctx context.Context, vector []float32, prompt string, response string, fingerprint string) error {
	tracer := otel.Tracer("qdrant-cache")
	ctx, span := tracer.Start(ctx, "QdrantSemanticCache.Save")
	defer span.End()

	url := fmt.Sprintf("%s/collections/%s/points?wait=true", c.url, c.collection)
	id := GenerateUUID()
	payload := map[string]interface{}{
		"prompt":      prompt,
		"response":    response,
		"timestamp":   time.Now().Unix(),
		"fingerprint": fingerprint,
	}
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
		span.RecordError(err)
		span.SetStatus(codes.Error, err.Error())
		return err
	}

	req, err := http.NewRequestWithContext(ctx, http.MethodPut, url, bytes.NewBuffer(bodyBytes))
	if err != nil {
		span.RecordError(err)
		span.SetStatus(codes.Error, err.Error())
		return err
	}
	c.addHeaders(req)

	resp, err := c.client.Do(req)
	if err != nil {
		span.RecordError(err)
		span.SetStatus(codes.Error, err.Error())
		return err
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		err := fmt.Errorf("upsert failed with status code: %d", resp.StatusCode)
		span.RecordError(err)
		span.SetStatus(codes.Error, err.Error())
		return err
	}
	return nil
}
