package aiorchestrator

import (
	"context"
	"crypto/rand"
	"crypto/sha256"
	"errors"
	"fmt"
	"math"
	"sort"
	"strings"
	"time"
)

type AIService struct {
	provider      LLMProviderPort
	repo          SessionRepositoryPort
	vectorRepo    VectorRepositoryPort
	cache         ResponseCachePort
	semanticCache SemanticCachePort
}

func NewAIService(provider LLMProviderPort, repo SessionRepositoryPort) *AIService {
	return &AIService{
		provider: provider,
		repo:     repo,
	}
}

func (s *AIService) SetVectorRepository(vr VectorRepositoryPort) {
	s.vectorRepo = vr
}

func (s *AIService) SetResponseCache(cache ResponseCachePort) {
	s.cache = cache
}

func (s *AIService) SetSemanticCache(sc SemanticCachePort) {
	s.semanticCache = sc
}

func (s *AIService) ListModels(ctx context.Context) ([]ModelInfo, error) {
	return s.provider.GetModels(ctx)
}

func generateCacheKey(modelID string, messages []ChatMessage) string {
	h := sha256.New()
	h.Write([]byte(modelID))
	for _, msg := range messages {
		h.Write([]byte(msg.Role))
		h.Write([]byte(msg.Content))
	}
	return fmt.Sprintf("%x", h.Sum(nil))
}

func (s *AIService) Chat(ctx context.Context, modelID string, messages []ChatMessage) (string, error) {
	cacheInfo := GetCacheInfo(ctx)

	var cacheKey string
	if s.cache != nil {
		cacheKey = generateCacheKey(modelID, messages)
		cachedVal, err := s.cache.Get(ctx, cacheKey)
		if err == nil && cachedVal != "" {
			if cacheInfo != nil {
				cacheInfo.Cached = true
				cacheInfo.CacheType = "standard"
			}
			return cachedVal, nil
		}
	}

	if s.semanticCache != nil {
		var lastUserMsg string
		for i := len(messages) - 1; i >= 0; i-- {
			if messages[i].Role == "user" {
				lastUserMsg = messages[i].Content
				break
			}
		}
		if lastUserMsg != "" {
			emb, err := s.provider.GenerateEmbedding(ctx, "@cf/baai/bge-small-en-v1.5", lastUserMsg)
			if err == nil && len(emb) > 0 {
				similarVal, err := s.semanticCache.GetSimilar(ctx, emb, 0.92)
				if err == nil && similarVal != "" {
					if cacheInfo != nil {
						cacheInfo.Cached = true
						cacheInfo.CacheType = "semantic"
					}
					if s.cache != nil && cacheKey != "" {
						_ = s.cache.Set(ctx, cacheKey, similarVal)
					}
					return similarVal, nil
				}
			}
		}
	}

	resp, err := s.provider.GenerateCompletion(ctx, modelID, messages)
	if err != nil {
		return "", err
	}

	if s.cache != nil && cacheKey != "" {
		_ = s.cache.Set(ctx, cacheKey, resp)
	}

	if s.semanticCache != nil {
		var lastUserMsg string
		for i := len(messages) - 1; i >= 0; i-- {
			if messages[i].Role == "user" {
				lastUserMsg = messages[i].Content
				break
			}
		}
		if lastUserMsg != "" {
			emb, err := s.provider.GenerateEmbedding(ctx, "@cf/baai/bge-small-en-v1.5", lastUserMsg)
			if err == nil && len(emb) > 0 {
				_ = s.semanticCache.Save(ctx, emb, lastUserMsg, resp)
			}
		}
	}

	if cacheInfo != nil {
		cacheInfo.Cached = false
		cacheInfo.CacheType = "none"
	}

	return resp, nil
}

func (s *AIService) PersistentChat(ctx context.Context, userID string, userMessage string, modelID string, embeddingModel string) (string, []ChatMessage, error) {
	if userID == "" {
		return "", nil, errors.New("user ID is required")
	}
	if userMessage == "" {
		return "", nil, errors.New("message is required")
	}
	if modelID == "" {
		return "", nil, errors.New("model ID is required")
	}

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

	var apiMessages []ChatMessage

	if s.vectorRepo != nil && len(userEmbedding) > 0 {
		matches, err := s.vectorRepo.Search(ctx, userID, userEmbedding, 3)
		if err == nil && len(matches) > 0 {
			var contextBuilder strings.Builder
			contextBuilder.WriteString("Relevant context from previous conversations:\n")
			for _, match := range matches {
				role := match.Payload["role"]
				content := match.Payload["content"]
				contextBuilder.WriteString(fmt.Sprintf("- %v: %v\n", role, content))
			}
			apiMessages = append(apiMessages, ChatMessage{
				Role:    "system",
				Content: contextBuilder.String(),
			})
		}
	} else if len(userEmbedding) > 0 && len(session.Messages) > 0 {
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
			apiMessages = append(apiMessages, ChatMessage{
				Role:    scored[i].msg.Role,
				Content: scored[i].msg.Content,
			})
		}
	}

	for _, msg := range session.Messages {
		apiMessages = append(apiMessages, ChatMessage{
			Role:    msg.Role,
			Content: msg.Content,
		})
	}

	apiMessages = append(apiMessages, ChatMessage{
		Role:    "user",
		Content: userMessage,
	})

	cacheInfo := GetCacheInfo(ctx)
	var cacheKey string
	var cachedVal string
	var cacheFound bool

	if s.cache != nil {
		cacheKey = generateCacheKey(modelID, apiMessages)
		val, err := s.cache.Get(ctx, cacheKey)
		if err == nil && val != "" {
			cachedVal = val
			cacheFound = true
			if cacheInfo != nil {
				cacheInfo.Cached = true
				cacheInfo.CacheType = "standard"
			}
		}
	}

	if !cacheFound && s.semanticCache != nil && len(userEmbedding) > 0 {
		val, err := s.semanticCache.GetSimilar(ctx, userEmbedding, 0.92)
		if err == nil && val != "" {
			cachedVal = val
			cacheFound = true
			if cacheInfo != nil {
				cacheInfo.Cached = true
				cacheInfo.CacheType = "semantic"
			}
			if s.cache != nil && cacheKey != "" {
				_ = s.cache.Set(ctx, cacheKey, val)
			}
		}
	}

	var completion string
	if cacheFound {
		completion = cachedVal
	} else {
		comp, err := s.provider.GenerateCompletion(ctx, modelID, apiMessages)
		if err != nil {
			return "", nil, err
		}
		completion = comp

		if s.cache != nil && cacheKey != "" {
			_ = s.cache.Set(ctx, cacheKey, completion)
		}
		if s.semanticCache != nil && len(userEmbedding) > 0 {
			_ = s.semanticCache.Save(ctx, userEmbedding, userMessage, completion)
		}
		if cacheInfo != nil {
			cacheInfo.Cached = false
			cacheInfo.CacheType = "none"
		}
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

	var assistantEmbedding []float32
	if embeddingModel != "" && len(userEmbedding) > 0 {
		asstEmb, err := s.provider.GenerateEmbedding(ctx, embeddingModel, completion)
		if err == nil {
			assistantEmbedding = asstEmb
			newAssistantMsg.Embedding = asstEmb
		}
	}

	session.Messages = append(session.Messages, newUserMsg, newAssistantMsg)

	err = s.repo.SaveSession(ctx, session)
	if err != nil {
		return "", nil, err
	}

	if s.vectorRepo != nil && len(userEmbedding) > 0 {
		userMsgID := generateUUID()
		userPayload := map[string]interface{}{
			"user_id":   userID,
			"role":      "user",
			"content":   userMessage,
			"timestamp": time.Now().Unix(),
		}
		_ = s.vectorRepo.Upsert(ctx, userMsgID, userEmbedding, userPayload)

		if len(assistantEmbedding) > 0 {
			asstMsgID := generateUUID()
			asstPayload := map[string]interface{}{
				"user_id":   userID,
				"role":      "assistant",
				"content":   completion,
				"timestamp": time.Now().Unix(),
			}
			_ = s.vectorRepo.Upsert(ctx, asstMsgID, assistantEmbedding, asstPayload)
		}
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

func generateUUID() string {
	b := make([]byte, 16)
	_, _ = rand.Read(b)
	b[6] = (b[6] & 0x0f) | 0x40
	b[8] = (b[8] & 0x3f) | 0x80
	return fmt.Sprintf("%x-%x-%x-%x-%x", b[0:4], b[4:6], b[6:8], b[8:10], b[10:])
}

