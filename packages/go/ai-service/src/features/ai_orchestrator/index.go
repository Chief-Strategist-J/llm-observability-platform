package aiorchestrator

import "context"

type Orchestrator interface {
	ListModels(ctx context.Context) ([]ModelInfo, error)
	Chat(ctx context.Context, modelID string, messages []ChatMessage) (string, error)
	PersistentChat(ctx context.Context, userID string, userMessage string, modelID string, embeddingModel string) (string, []ChatMessage, error)
}

func New(provider LLMProviderPort, repo SessionRepositoryPort) Orchestrator {
	return NewAIService(provider, repo)
}
