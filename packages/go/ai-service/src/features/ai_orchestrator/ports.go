package aiorchestrator

import "context"

type LLMProviderPort interface {
	GetModels(ctx context.Context) ([]ModelInfo, error)
	GenerateCompletion(ctx context.Context, modelID string, messages []ChatMessage) (string, error)
	GenerateEmbedding(ctx context.Context, modelID string, text string) ([]float32, error)
}

type SessionRepositoryPort interface {
	GetSession(ctx context.Context, userID string) (*ChatSession, error)
	SaveSession(ctx context.Context, session *ChatSession) error
	DeleteSession(ctx context.Context, userID string) error
}

type SearchResult struct {
	ID      string                 `json:"id"`
	Score   float32                `json:"score"`
	Payload map[string]interface{} `json:"payload"`
}

type VectorRepositoryPort interface {
	Search(ctx context.Context, userID string, vector []float32, limit int) ([]SearchResult, error)
	Upsert(ctx context.Context, id string, vector []float32, payload map[string]interface{}) error
}

