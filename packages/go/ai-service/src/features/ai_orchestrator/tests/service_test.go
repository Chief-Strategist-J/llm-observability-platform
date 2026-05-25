package tests

import (
	"context"
	"errors"
	"os"
	"strings"
	"testing"
	"time"

	aiorchestrator "github.com/llm-observability/platform/packages/go/ai-service/src/features/ai_orchestrator"
)

type mockLLMProvider struct {
	models             []aiorchestrator.ModelInfo
	completion         string
	embedding          []float32
	getErr             error
	chatErr            error
	embedErr           error
	lastModelID        string
	completionsHistory []string
}

func (m *mockLLMProvider) GetModels(ctx context.Context) ([]aiorchestrator.ModelInfo, error) {
	return m.models, m.getErr
}

func (m *mockLLMProvider) GenerateCompletion(ctx context.Context, modelID string, messages []aiorchestrator.ChatMessage) (string, error) {
	m.lastModelID = modelID
	if len(messages) > 0 {
		m.completionsHistory = append(m.completionsHistory, messages[len(messages)-1].Content)
	}
	if strings.Contains(modelID, "small") || strings.Contains(modelID, "awq") {
		if len(messages) > 0 && strings.Contains(messages[0].Content, "Classify") {
			if strings.Contains(messages[1].Content, "complex query") {
				return "complex", nil
			}
			return "simple", nil
		}
	}
	if len(messages) > 0 && strings.Contains(messages[0].Content, "fact extraction assistant") {
		return `[{"fact": "fact 1", "importance": 3}, {"fact": "fact 2", "importance": 5}]`, nil
	}
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

	time.Sleep(50 * time.Millisecond)

	if vectorRepo.upsertCalled != 2 {
		t.Errorf("expected 2 upserts, got %d", vectorRepo.upsertCalled)
	}

	if len(history) != 2 {
		t.Errorf("expected history length 2, got %d", len(history))
	}
}

type mockResponseCache struct {
	store  map[string]string
	getErr error
	setErr error
}

func (m *mockResponseCache) Get(ctx context.Context, key string) (string, error) {
	if m.getErr != nil {
		return "", m.getErr
	}
	return m.store[key], nil
}

func (m *mockResponseCache) Set(ctx context.Context, key string, value string) error {
	if m.setErr != nil {
		return m.setErr
	}
	m.store[key] = value
	return nil
}

type mockSemanticCache struct {
	similarResponse string
	getErr          error
	saveErr         error
	savedVector     []float32
	savedPrompt     string
	savedResponse   string
	savedFingerprint string
	lastFingerprint string
}

func (m *mockSemanticCache) GetSimilar(ctx context.Context, vector []float32, threshold float32, fingerprint string) (string, error) {
	m.lastFingerprint = fingerprint
	if m.getErr != nil {
		return "", m.getErr
	}
	return m.similarResponse, nil
}

func (m *mockSemanticCache) Save(ctx context.Context, vector []float32, prompt string, response string, fingerprint string) error {
	if m.saveErr != nil {
		return m.saveErr
	}
	m.savedVector = vector
	m.savedPrompt = prompt
	m.savedResponse = response
	m.savedFingerprint = fingerprint
	return nil
}

func TestChatCache(t *testing.T) {
	provider := &mockLLMProvider{
		completion: "fresh response",
		embedding:  []float32{0.1, 0.2},
	}
	repo := &mockSessionRepository{}
	service := aiorchestrator.New(provider, repo)

	cache := &mockResponseCache{store: make(map[string]string)}
	semCache := &mockSemanticCache{}

	if s, ok := service.(*aiorchestrator.AIService); ok {
		s.SetResponseCache(cache)
		s.SetSemanticCache(semCache)
	}

	ctx, cacheInfo := aiorchestrator.WithCacheInfo(context.Background())
	resp, err := service.Chat(ctx, "test-model", []aiorchestrator.ChatMessage{{Role: "user", Content: "hello"}})
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if resp != "fresh response" {
		t.Errorf("expected fresh response, got %s", resp)
	}
	if cacheInfo.Cached {
		t.Error("expected cache miss")
	}

	ctx, cacheInfo = aiorchestrator.WithCacheInfo(context.Background())
	resp, err = service.Chat(ctx, "test-model", []aiorchestrator.ChatMessage{{Role: "user", Content: "hello"}})
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if resp != "fresh response" {
		t.Errorf("expected cached response to match, got %s", resp)
	}
	if !cacheInfo.Cached || cacheInfo.CacheType != "standard" {
		t.Errorf("expected standard cache hit, got Cached=%t, Type=%s", cacheInfo.Cached, cacheInfo.CacheType)
	}

	semCache.similarResponse = "semantic similarity hit"
	ctx, cacheInfo = aiorchestrator.WithCacheInfo(context.Background())
	resp, err = service.Chat(ctx, "test-model", []aiorchestrator.ChatMessage{{Role: "user", Content: "hello brand new"}})
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if resp != "semantic similarity hit" {
		t.Errorf("expected semantic similarity hit, got %s", resp)
	}
	if !cacheInfo.Cached || cacheInfo.CacheType != "semantic" {
		t.Errorf("expected semantic cache hit, got Cached=%t, Type=%s", cacheInfo.Cached, cacheInfo.CacheType)
	}
}

func TestPersistentChatCache(t *testing.T) {
	provider := &mockLLMProvider{
		completion: "chat raw response",
		embedding:  []float32{0.5, 0.5},
	}
	repo := &mockSessionRepository{
		sessions: make(map[string]*aiorchestrator.ChatSession),
	}
	service := aiorchestrator.New(provider, repo)

	cache := &mockResponseCache{store: make(map[string]string)}
	semCache := &mockSemanticCache{}

	if s, ok := service.(*aiorchestrator.AIService); ok {
		s.SetResponseCache(cache)
		s.SetSemanticCache(semCache)
	}

	ctx, cacheInfo := aiorchestrator.WithCacheInfo(context.Background())
	resp, _, err := service.PersistentChat(ctx, "user-1", "hello", "test-model", "embed-model")
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if resp != "chat raw response" {
		t.Errorf("expected raw response, got %s", resp)
	}
	if cacheInfo.Cached {
		t.Error("expected cache miss")
	}

	ctx, cacheInfo = aiorchestrator.WithCacheInfo(context.Background())
	resp, _, err = service.PersistentChat(ctx, "user-2", "hello", "test-model", "embed-model")
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if resp != "chat raw response" {
		t.Errorf("expected cached response, got %s", resp)
	}
	if !cacheInfo.Cached || cacheInfo.CacheType != "standard" {
		t.Errorf("expected standard cache hit, got Cached=%t, Type=%s", cacheInfo.Cached, cacheInfo.CacheType)
	}
}

func TestPromptFingerprintingAndGating(t *testing.T) {
	provider := &mockLLMProvider{
		completion: "fresh output",
		embedding:  []float32{0.1, 0.2},
	}
	repo := &mockSessionRepository{}
	service := aiorchestrator.New(provider, repo)

	semCache := &mockSemanticCache{}
	if s, ok := service.(*aiorchestrator.AIService); ok {
		s.SetSemanticCache(semCache)
	}

	ctx := context.Background()
	_, _ = service.Chat(ctx, "model-A", []aiorchestrator.ChatMessage{
		{Role: "system", Content: "sys-A"},
		{Role: "user", Content: "user-msg-content"},
	})

	fingerprintA := semCache.savedFingerprint
	if fingerprintA == "" {
		t.Error("expected fingerprint to be saved")
	}

	_, _ = service.Chat(ctx, "model-A", []aiorchestrator.ChatMessage{
		{Role: "system", Content: "sys-B"},
		{Role: "user", Content: "user-msg-content"},
	})

	fingerprintB := semCache.savedFingerprint
	if fingerprintA == fingerprintB {
		t.Error("expected different fingerprint for different system message")
	}
}

func TestModelRoutingClassifierSimpleComplex(t *testing.T) {
	_ = os.Setenv("AI_SMALL_MODEL", "model-small")
	_ = os.Setenv("AI_LARGE_MODEL", "model-large")
	defer func() {
		_ = os.Unsetenv("AI_SMALL_MODEL")
		_ = os.Unsetenv("AI_LARGE_MODEL")
	}()

	provider := &mockLLMProvider{
		completion: "output-simple",
		embedding:  []float32{0.1, 0.2},
	}
	repo := &mockSessionRepository{}
	service := aiorchestrator.New(provider, repo)

	ctx := context.Background()
	_, _ = service.Chat(ctx, "default-model", []aiorchestrator.ChatMessage{
		{Role: "user", Content: "short"},
	})
	if provider.lastModelID != "model-small" {
		t.Errorf("expected routing to small model for short query, got %s", provider.lastModelID)
	}

	provider.completion = "output-complex"
	_, _ = service.Chat(ctx, "default-model", []aiorchestrator.ChatMessage{
		{Role: "user", Content: "this is a complex query to route with architecture optimize"},
	})
	if provider.lastModelID != "model-large" {
		t.Errorf("expected routing to large model for complex query, got %s", provider.lastModelID)
	}
}

func TestHistoryCompaction(t *testing.T) {
	_ = os.Setenv("AI_COMPACTION_THRESHOLD", "10")
	defer func() {
		_ = os.Unsetenv("AI_COMPACTION_THRESHOLD")
	}()

	provider := &mockLLMProvider{
		completion: "summary content",
		embedding:  []float32{0.1, 0.2},
	}
	repo := &mockSessionRepository{
		sessions: map[string]*aiorchestrator.ChatSession{
			"user-1": {
				UserID: "user-1",
				Messages: []aiorchestrator.ChatMessage{
					{Role: "user", Content: "m1"},
					{Role: "assistant", Content: "m2"},
					{Role: "user", Content: "m3"},
					{Role: "assistant", Content: "m4"},
					{Role: "user", Content: "m5"},
					{Role: "assistant", Content: "m6"},
					{Role: "user", Content: "m7"},
					{Role: "assistant", Content: "m8"},
					{Role: "user", Content: "m9"},
					{Role: "assistant", Content: "m10"},
					{Role: "user", Content: "m11"},
				},
				LastAccessedAt: time.Now(),
			},
		},
	}
	service := aiorchestrator.New(provider, repo)

	_, _, err := service.PersistentChat(context.Background(), "user-1", "m12", "model-A", "embed-model")
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}

	time.Sleep(50 * time.Millisecond)

	session, err := repo.GetSession(context.Background(), "user-1")
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	history := session.Messages

	if len(history) <= 4 {
		t.Errorf("unexpected short history: %d", len(history))
	}

	foundSummary := false
	for _, msg := range history {
		if strings.Contains(msg.Content, "Summary of older conversation") {
			foundSummary = true
			break
		}
	}
	if !foundSummary {
		t.Error("expected compacted summary message in history")
	}
}
