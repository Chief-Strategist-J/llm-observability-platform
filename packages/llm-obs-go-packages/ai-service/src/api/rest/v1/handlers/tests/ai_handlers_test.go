package tests

import (
	"bytes"
	"context"
	"encoding/json"
	"errors"
	"net/http"
	"net/http/httptest"
	"testing"

	"github.com/llm-observability/platform/packages/go/ai-service/src/api/rest/v1/handlers"
	aiorchestrator "github.com/llm-observability/platform/packages/go/ai-service/src/features/ai_orchestrator"
)

type mockOrchestrator struct {
	models     []aiorchestrator.ModelInfo
	listErr    error
	completion string
	chatErr    error
	persErr    error
}

func (m *mockOrchestrator) ListModels(ctx context.Context) ([]aiorchestrator.ModelInfo, error) {
	return m.models, m.listErr
}

func (m *mockOrchestrator) Chat(ctx context.Context, modelID string, messages []aiorchestrator.ChatMessage) (string, error) {
	return m.completion, m.chatErr
}

func (m *mockOrchestrator) PersistentChat(ctx context.Context, userID, userMessage, modelID, embeddingModel string) (string, []aiorchestrator.ChatMessage, error) {
	if m.persErr != nil {
		return "", nil, m.persErr
	}
	history := []aiorchestrator.ChatMessage{
		{Role: "user", Content: userMessage},
		{Role: "assistant", Content: m.completion},
	}
	return m.completion, history, nil
}

func TestListModelsHandler(t *testing.T) {
	orch := &mockOrchestrator{
		models: []aiorchestrator.ModelInfo{
			{ID: "m1", Name: "Model 1"},
		},
	}
	h := handlers.NewAIHandlers(orch)

	req := httptest.NewRequest(http.MethodGet, "/api/v1/models", nil)
	w := httptest.NewRecorder()

	h.ListModels(w, req)

	if w.Code != http.StatusOK {
		t.Errorf("expected 200, got %d", w.Code)
	}

	var res []aiorchestrator.ModelInfo
	if err := json.NewDecoder(w.Body).Decode(&res); err != nil {
		t.Fatalf("failed to decode response: %v", err)
	}

	if len(res) != 1 || res[0].ID != "m1" {
		t.Errorf("unexpected body: %v", res)
	}
}

func TestListModelsHandlerError(t *testing.T) {
	orch := &mockOrchestrator{listErr: errors.New("provider error")}
	h := handlers.NewAIHandlers(orch)

	req := httptest.NewRequest(http.MethodGet, "/api/v1/models", nil)
	w := httptest.NewRecorder()

	h.ListModels(w, req)

	if w.Code != http.StatusInternalServerError {
		t.Errorf("expected 500, got %d", w.Code)
	}
}

func TestChatHandler(t *testing.T) {
	orch := &mockOrchestrator{completion: "ai reply"}
	h := handlers.NewAIHandlers(orch)

	body := map[string]interface{}{
		"model": "m1",
		"messages": []map[string]string{
			{"role": "user", "content": "hi"},
		},
	}
	bodyBytes, _ := json.Marshal(body)

	req := httptest.NewRequest(http.MethodPost, "/api/v1/chat", bytes.NewBuffer(bodyBytes))
	w := httptest.NewRecorder()

	h.Chat(w, req)

	if w.Code != http.StatusOK {
		t.Errorf("expected 200, got %d", w.Code)
	}

	var res map[string]string
	json.NewDecoder(w.Body).Decode(&res)

	if res["response"] != "ai reply" {
		t.Errorf("expected 'ai reply', got '%s'", res["response"])
	}
}

func TestChatHandlerInvalidJSON(t *testing.T) {
	h := handlers.NewAIHandlers(&mockOrchestrator{})

	req := httptest.NewRequest(http.MethodPost, "/api/v1/chat", bytes.NewBufferString("{invalid"))
	w := httptest.NewRecorder()

	h.Chat(w, req)

	if w.Code != http.StatusBadRequest {
		t.Errorf("expected 400, got %d", w.Code)
	}
}

func TestPersistentChatHandler(t *testing.T) {
	orch := &mockOrchestrator{completion: "hello persistent"}
	h := handlers.NewAIHandlers(orch)

	body := map[string]interface{}{
		"user_id": "u1",
		"message": "how are you?",
	}
	bodyBytes, _ := json.Marshal(body)

	req := httptest.NewRequest(http.MethodPost, "/api/v1/chat/persistent", bytes.NewBuffer(bodyBytes))
	w := httptest.NewRecorder()

	h.PersistentChat(w, req)

	if w.Code != http.StatusOK {
		t.Errorf("expected 200, got %d", w.Code)
	}

	var res map[string]interface{}
	json.NewDecoder(w.Body).Decode(&res)

	if res["response"] != "hello persistent" {
		t.Errorf("expected response, got %v", res)
	}
}

func TestPersistentChatHandlerMissingParams(t *testing.T) {
	h := handlers.NewAIHandlers(&mockOrchestrator{})

	body := map[string]interface{}{
		"user_id": "",
		"message": "hello",
	}
	bodyBytes, _ := json.Marshal(body)

	req := httptest.NewRequest(http.MethodPost, "/api/v1/chat/persistent", bytes.NewBuffer(bodyBytes))
	w := httptest.NewRecorder()

	h.PersistentChat(w, req)

	if w.Code != http.StatusBadRequest {
		t.Errorf("expected 400 for empty user_id, got %d", w.Code)
	}
}
