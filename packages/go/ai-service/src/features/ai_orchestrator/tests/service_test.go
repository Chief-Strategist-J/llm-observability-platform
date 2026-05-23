package tests

import (
	"context"
	"errors"
	"testing"
	"time"

	aiorchestrator "github.com/llm-observability/platform/packages/go/ai-service/src/features/ai_orchestrator"
)

type mockLLMProvider struct {
	models      []aiorchestrator.ModelInfo
	completion  string
	embedding   []float32
	getErr      error
	chatErr     error
	embedErr    error
}

func (m *mockLLMProvider) GetModels(ctx context.Context) ([]aiorchestrator.ModelInfo, error) {
	return m.models, m.getErr
}

func (m *mockLLMProvider) GenerateCompletion(ctx context.Context, modelID string, messages []aiorchestrator.ChatMessage) (string, error) {
	return m.completion, m.chatErr
}

func (m *mockLLMProvider) GenerateEmbedding(ctx context.Context, modelID string, text string) ([]float32, error) {
	return m.embedding, m.embedErr
}

type mockSessionRepository struct {
	sessions map[string]*aiorchestrator.ChatSession
	getErr   error
	saveErr  error
	delErr   error
}

func (m *mockSessionRepository) GetSession(ctx context.Context, userID string) (*aiorchestrator.ChatSession, error) {
	if m.getErr != nil {
		return nil, m.getErr
	}
	return m.sessions[userID], nil
}

func (m *mockSessionRepository) SaveSession(ctx context.Context, session *aiorchestrator.ChatSession) error {
	if m.saveErr != nil {
		return m.saveErr
	}
	m.sessions[session.UserID] = session
	return nil
}

func (m *mockSessionRepository) DeleteSession(ctx context.Context, userID string) error {
	if m.delErr != nil {
		return m.delErr
	}
	delete(m.sessions, userID)
	return nil
}

func TestListModels(t *testing.T) {
	expectedModels := []aiorchestrator.ModelInfo{
		{ID: "test-model", Name: "Test Model"},
	}
	provider := &mockLLMProvider{models: expectedModels}
	repo := &mockSessionRepository{}
	service := aiorchestrator.New(provider, repo)

	models, err := service.ListModels(context.Background())
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}

	if len(models) != 1 || models[0].ID != "test-model" {
		t.Errorf("unexpected models returned: %v", models)
	}
}

func TestChat(t *testing.T) {
	provider := &mockLLMProvider{completion: "hello response"}
	repo := &mockSessionRepository{}
	service := aiorchestrator.New(provider, repo)

	resp, err := service.Chat(context.Background(), "test-model", []aiorchestrator.ChatMessage{})
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}

	if resp != "hello response" {
		t.Errorf("expected 'hello response', got '%s'", resp)
	}
}

func TestPersistentChat(t *testing.T) {
	provider := &mockLLMProvider{
		completion: "answer",
		embedding:  []float32{1.0, 0.0, 0.0},
	}
	repo := &mockSessionRepository{
		sessions: make(map[string]*aiorchestrator.ChatSession),
	}
	service := aiorchestrator.New(provider, repo)

	resp, history, err := service.PersistentChat(context.Background(), "user-1", "hello", "test-model", "embed-model")
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}

	if resp != "answer" {
		t.Errorf("expected 'answer', got '%s'", resp)
	}

	if len(history) != 2 {
		t.Errorf("expected 2 messages in history, got %d", len(history))
	}

	if history[0].Role != "user" || history[0].Content != "hello" {
		t.Errorf("unexpected first message: %v", history[0])
	}

	if history[1].Role != "assistant" || history[1].Content != "answer" {
		t.Errorf("unexpected second message: %v", history[1])
	}
}

func TestPersistentChatWithHistoryContext(t *testing.T) {
	provider := &mockLLMProvider{
		completion: "answer2",
		embedding:  []float32{1.0, 0.0, 0.0},
	}
	repo := &mockSessionRepository{
		sessions: map[string]*aiorchestrator.ChatSession{
			"user-1": {
				UserID: "user-1",
				Messages: []aiorchestrator.ChatMessage{
					{
						Role:      "user",
						Content:   "previous hello",
						Embedding: []float32{0.9, 0.1, 0.0},
					},
				},
				LastAccessedAt: time.Now(),
			},
		},
	}
	service := aiorchestrator.New(provider, repo)

	_, history, err := service.PersistentChat(context.Background(), "user-1", "hello", "test-model", "embed-model")
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}

	if len(history) != 3 {
		t.Errorf("expected 3 messages in history, got %d", len(history))
	}
}

func TestGetSessionErrors(t *testing.T) {
	provider := &mockLLMProvider{}
	repo := &mockSessionRepository{
		getErr: errors.New("db error"),
	}
	service := aiorchestrator.New(provider, repo)

	_, _, err := service.PersistentChat(context.Background(), "user-1", "hello", "test-model", "embed-model")
	if err == nil {
		t.Error("expected error, got nil")
	}
}

type mockVectorRepository struct {
	searchResult []aiorchestrator.SearchResult
	searchCalled bool
	upsertCalled int
	upsertData   []struct {
		id      string
		vector  []float32
		payload map[string]interface{}
	}
}

func (m *mockVectorRepository) Search(ctx context.Context, userID string, vector []float32, limit int) ([]aiorchestrator.SearchResult, error) {
	m.searchCalled = true
	return m.searchResult, nil
}

func (m *mockVectorRepository) Upsert(ctx context.Context, id string, vector []float32, payload map[string]interface{}) error {
	m.upsertCalled++
	m.upsertData = append(m.upsertData, struct {
		id      string
		vector  []float32
		payload map[string]interface{}
	}{id: id, vector: vector, payload: payload})
	return nil
}

func TestPersistentChatWithVectorRepo(t *testing.T) {
	provider := &mockLLMProvider{
		completion: "assistant response",
		embedding:  []float32{0.5, 0.5},
	}
	repo := &mockSessionRepository{
		sessions: make(map[string]*aiorchestrator.ChatSession),
	}
	vectorRepo := &mockVectorRepository{
		searchResult: []aiorchestrator.SearchResult{
			{
				ID:    "old-uuid",
				Score: 0.99,
				Payload: map[string]interface{}{
					"role":    "user",
					"content": "past context",
				},
			},
		},
	}

	service := aiorchestrator.New(provider, repo)
	if s, ok := service.(*aiorchestrator.AIService); ok {
		s.SetVectorRepository(vectorRepo)
	}

	resp, history, err := service.PersistentChat(context.Background(), "user-123", "new message", "test-model", "embed-model")
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}

	if resp != "assistant response" {
		t.Errorf("expected 'assistant response', got '%s'", resp)
	}

	if !vectorRepo.searchCalled {
		t.Error("expected vector search to be called")
	}

	if vectorRepo.upsertCalled != 2 {
		t.Errorf("expected 2 upserts (user + assistant), got %d", vectorRepo.upsertCalled)
	}

	if len(history) != 2 {
		t.Errorf("expected history length 2, got %d", len(history))
	}
}

