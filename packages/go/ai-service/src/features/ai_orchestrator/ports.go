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
