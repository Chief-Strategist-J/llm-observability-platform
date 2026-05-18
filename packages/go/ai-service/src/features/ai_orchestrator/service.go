package aiorchestrator

import (
	"context"
	"math"
	"sort"
	"time"
)

type AIService struct {
	provider LLMProviderPort
	repo     SessionRepositoryPort
}

func NewAIService(provider LLMProviderPort, repo SessionRepositoryPort) *AIService {
	return &AIService{
		provider: provider,
		repo:     repo,
	}
}

func (s *AIService) ListModels(ctx context.Context) ([]ModelInfo, error) {
	return s.provider.GetModels(ctx)
}

func (s *AIService) Chat(ctx context.Context, modelID string, messages []ChatMessage) (string, error) {
	return s.provider.GenerateCompletion(ctx, modelID, messages)
}

func (s *AIService) PersistentChat(ctx context.Context, userID string, userMessage string, modelID string, embeddingModel string) (string, []ChatMessage, error) {
	session, err := s.repo.GetSession(ctx, userID)
	if err != nil {
		return "", nil, err
	}
	if session == nil {
		session = &ChatSession{
			UserID:         userID,
			Messages:       []ChatMessage{},
			LastAccessedAt: time.Now(),
		}
	}

	session.LastAccessedAt = time.Now()

	var userEmbedding []float32
	if embeddingModel != "" {
		emb, err := s.provider.GenerateEmbedding(ctx, embeddingModel, userMessage)
		if err == nil {
			userEmbedding = emb
		}
	}

	var contextMessages []ChatMessage
	if len(userEmbedding) > 0 && len(session.Messages) > 0 {
		type scoredMessage struct {
			msg   ChatMessage
			score float64
		}
		var scored []scoredMessage
		for _, m := range session.Messages {
			if len(m.Embedding) > 0 {
				score := cosineSimilarity(userEmbedding, m.Embedding)
				scored = append(scored, scoredMessage{msg: m, score: score})
			}
		}

		sort.Slice(scored, func(i, j int) bool {
			return scored[i].score > scored[j].score
		})

		limit := 3
		if len(scored) < limit {
			limit = len(scored)
		}
		for i := 0; i < limit; i++ {
			contextMessages = append(contextMessages, scored[i].msg)
		}
	}

	var apiMessages []ChatMessage
	for _, cm := range contextMessages {
		apiMessages = append(apiMessages, ChatMessage{
			Role:    cm.Role,
			Content: cm.Content,
		})
	}
	apiMessages = append(apiMessages, ChatMessage{
		Role:    "user",
		Content: userMessage,
	})

	completion, err := s.provider.GenerateCompletion(ctx, modelID, apiMessages)
	if err != nil {
		return "", nil, err
	}

	newUserMsg := ChatMessage{
		Role:      "user",
		Content:   userMessage,
		Embedding: userEmbedding,
	}

	newAssistantMsg := ChatMessage{
		Role:    "assistant",
		Content: completion,
	}

	if embeddingModel != "" && len(userEmbedding) > 0 {
		asstEmb, err := s.provider.GenerateEmbedding(ctx, embeddingModel, completion)
		if err == nil {
			newAssistantMsg.Embedding = asstEmb
		}
	}

	session.Messages = append(session.Messages, newUserMsg, newAssistantMsg)

	err = s.repo.SaveSession(ctx, session)
	if err != nil {
		return "", nil, err
	}

	return completion, session.Messages, nil
}

func cosineSimilarity(a, b []float32) float64 {
	if len(a) != len(b) || len(a) == 0 {
		return 0.0
	}
	var dotProduct, normA, normB float64
	for i := 0; i < len(a); i++ {
		dotProduct += float64(a[i] * b[i])
		normA += float64(a[i] * a[i])
		normB += float64(b[i] * b[i])
	}
	if normA == 0.0 || normB == 0.0 {
		return 0.0
	}
	return dotProduct / (math.Sqrt(normA) * math.Sqrt(normB))
}
