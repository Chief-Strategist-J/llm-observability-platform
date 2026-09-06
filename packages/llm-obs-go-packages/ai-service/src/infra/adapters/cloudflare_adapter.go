package adapters

import (
	"bytes"
	"context"
	"crypto/sha256"
	"encoding/binary"
	"encoding/json"
	"errors"
	"fmt"
	"net/http"
	"os"
	"strings"
	"time"

	aiorchestrator "github.com/llm-observability/platform/packages/go/ai-service/src/features/ai_orchestrator"
)

type CloudflareAdapter struct {
	accountID string
	apiToken  string
	accessJWT string
	client    *http.Client
}

func NewCloudflareAdapter(accountID, apiToken string) *CloudflareAdapter {
	return &CloudflareAdapter{
		accountID: strings.TrimSpace(accountID),
		apiToken:  strings.TrimSpace(apiToken),
		accessJWT: strings.TrimSpace(os.Getenv("CF_ACCESS_JWT_ASSERTION")),
		client: &http.Client{
			Timeout: 30 * time.Second,
		},
	}
}

type cfSearchResponse struct {
	Success bool                       `json:"success"`
	Result  []aiorchestrator.ModelInfo `json:"result"`
}

type cfRunChatResponse struct {
	Success bool `json:"success"`
	Result  struct {
		Response string `json:"response"`
	} `json:"result"`
}

type cfRunEmbeddingResponse struct {
	Success bool `json:"success"`
	Result  struct {
		Data [][]float32 `json:"data"`
	} `json:"result"`
}

func (a *CloudflareAdapter) isMock() bool {
	return a.accountID == "" || a.apiToken == "" || a.accountID == "local-account"
}

func (a *CloudflareAdapter) addHeaders(req *http.Request) {
	req.Header.Set("Authorization", "Bearer "+a.apiToken)
	req.Header.Set("Content-Type", "application/json")
	if a.accessJWT != "" {
		req.Header.Set("CF-Access-JWT-Assertion", a.accessJWT)
	}
}

func (a *CloudflareAdapter) GetModels(ctx context.Context) ([]aiorchestrator.ModelInfo, error) {
	if a.isMock() {
		return []aiorchestrator.ModelInfo{
			{
				ID:          "@cf/meta/llama-3.1-8b-instruct",
				Name:        "Llama 3.1 8B Instruct",
				Description: "Meta Llama 3.1 8B Instruct model",
				Provider:    "cloudflare",
			},
			{
				ID:          "@cf/google/gemma-3-12b-it",
				Name:        "Gemma 3 12B IT",
				Description: "Google Gemma 3 12B IT model",
				Provider:    "cloudflare",
			},
			{
				ID:          "@cf/baai/bge-small-en-v1.5",
				Name:        "BGE Small EN v1.5",
				Description: "BAAI BGE Small EN v1.5 embedding model",
				Provider:    "cloudflare",
			},
		}, nil
	}

	url := fmt.Sprintf("https://api.cloudflare.com/client/v4/accounts/%s/ai/models/search", a.accountID)
	req, err := http.NewRequestWithContext(ctx, http.MethodGet, url, nil)
	if err != nil {
		return nil, err
	}

	a.addHeaders(req)

	resp, err := a.client.Do(req)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("unexpected status code: %d", resp.StatusCode)
	}

	var cfResp cfSearchResponse
	if err := json.NewDecoder(resp.Body).Decode(&cfResp); err != nil {
		return nil, err
	}

	if !cfResp.Success {
		return nil, errors.New("cloudflare request not successful")
	}

	return cfResp.Result, nil
}

func (a *CloudflareAdapter) GenerateCompletion(ctx context.Context, modelID string, messages []aiorchestrator.ChatMessage) (string, error) {
	if a.isMock() {
		lastMsg := "hello"
		if len(messages) > 0 {
			lastMsg = messages[len(messages)-1].Content
		}
		return "[Mock Response for " + modelID + "] I received your query: " + lastMsg, nil
	}

	url := fmt.Sprintf("https://api.cloudflare.com/client/v4/accounts/%s/ai/run/%s", a.accountID, modelID)

	type msgDTO struct {
		Role    string `json:"role"`
		Content string `json:"content"`
	}
	var dtos []msgDTO
	for _, m := range messages {
		dtos = append(dtos, msgDTO{Role: m.Role, Content: m.Content})
	}

	bodyMap := map[string]interface{}{
		"messages": dtos,
	}

	jsonBytes, err := json.Marshal(bodyMap)
	if err != nil {
		return "", err
	}

	req, err := http.NewRequestWithContext(ctx, http.MethodPost, url, bytes.NewBuffer(jsonBytes))
	if err != nil {
		return "", err
	}

	a.addHeaders(req)

	resp, err := a.client.Do(req)
	if err != nil {
		return "", err
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return "", fmt.Errorf("unexpected status code: %d", resp.StatusCode)
	}

	var cfResp cfRunChatResponse
	if err := json.NewDecoder(resp.Body).Decode(&cfResp); err != nil {
		return "", err
	}

	if !cfResp.Success {
		return "", errors.New("cloudflare inference run failed")
	}

	return cfResp.Result.Response, nil
}

func (a *CloudflareAdapter) GenerateEmbedding(ctx context.Context, modelID string, text string) ([]float32, error) {
	if a.isMock() {
		hasher := sha256.New()
		hasher.Write([]byte(text))
		sum := hasher.Sum(nil)
		emb := make([]float32, 384)
		for i := 0; i < len(emb); i++ {
			idx := (i * 4) % len(sum)
			chunk := sum[idx : idx+4]
			val := binary.LittleEndian.Uint32(chunk)
			emb[i] = float32(val) / float32(mathMaxUint32)
		}
		return emb, nil
	}

	url := fmt.Sprintf("https://api.cloudflare.com/client/v4/accounts/%s/ai/run/%s", a.accountID, modelID)

	bodyMap := map[string]interface{}{
		"text": []string{text},
	}

	jsonBytes, err := json.Marshal(bodyMap)
	if err != nil {
		return nil, err
	}

	req, err := http.NewRequestWithContext(ctx, http.MethodPost, url, bytes.NewBuffer(jsonBytes))
	if err != nil {
		return nil, err
	}

	a.addHeaders(req)

	resp, err := a.client.Do(req)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("unexpected status code: %d", resp.StatusCode)
	}

	var cfResp cfRunEmbeddingResponse
	if err := json.NewDecoder(resp.Body).Decode(&cfResp); err != nil {
		return nil, err
	}

	if !cfResp.Success {
		return nil, errors.New("cloudflare embedding run failed")
	}

	if len(cfResp.Result.Data) == 0 {
		return nil, errors.New("empty embedding result from cloudflare")
	}

	return cfResp.Result.Data[0], nil
}

const mathMaxUint32 = 4294967295
