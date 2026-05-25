package aiorchestrator

import (
	"context"
	"crypto/rand"
	"crypto/sha256"
	"encoding/json"
	"errors"
	"fmt"
	"math"
	"os"
	"sort"
	"strconv"
	"strings"
	"sync"
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

func generatePromptFingerprint(modelID string, messages []ChatMessage) string {
	if len(messages) <= 1 {
		return fmt.Sprintf("model:%s:no-context", modelID)
	}
	h := sha256.New()
	h.Write([]byte(modelID))
	for i := 0; i < len(messages)-1; i++ {
		h.Write([]byte(messages[i].Role))
		h.Write([]byte(messages[i].Content))
	}
	return fmt.Sprintf("%x", h.Sum(nil))
}

func getFloatEnv(key string, defaultValue float64) float64 {
	valStr := os.Getenv(key)
	if valStr == "" {
		return defaultValue
	}
	val, err := strconv.ParseFloat(valStr, 64)
	if err != nil {
		return defaultValue
	}
	return val
}

func getIntEnv(key string, defaultValue int) int {
	valStr := os.Getenv(key)
	if valStr == "" {
		return defaultValue
	}
	val, err := strconv.Atoi(valStr)
	if err != nil {
		return defaultValue
	}
	return val
}

func (s *AIService) Chat(ctx context.Context, modelID string, messages []ChatMessage) (string, error) {
	cacheInfo := GetCacheInfo(ctx)

	var cacheKey string
	if s.cache != nil {
		cacheKey = "stateless:" + generateCacheKey(modelID, messages)
		cachedVal, err := s.cache.Get(ctx, cacheKey)
		if err == nil && cachedVal != "" {
			if cacheInfo != nil {
				cacheInfo.Cached = true
				cacheInfo.CacheType = "standard"
			}
			return cachedVal, nil
		}
	}

	fingerprint := generatePromptFingerprint(modelID, messages)

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
				threshold := float32(getFloatEnv("AI_SEMANTIC_CACHE_THRESHOLD", 0.90))
				similarVal, err := s.semanticCache.GetSimilar(ctx, emb, threshold, fingerprint)
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

	var lastUserMsg string
	for i := len(messages) - 1; i >= 0; i-- {
		if messages[i].Role == "user" {
			lastUserMsg = messages[i].Content
			break
		}
	}

	routedModel := s.classifyAndRoute(ctx, lastUserMsg, modelID)

	resp, err := s.provider.GenerateCompletion(ctx, routedModel, messages)
	if err != nil {
		return "", err
	}

	if s.cache != nil && cacheKey != "" {
		_ = s.cache.Set(ctx, cacheKey, resp)
	}

	if s.semanticCache != nil && lastUserMsg != "" {
		emb, err := s.provider.GenerateEmbedding(ctx, "@cf/baai/bge-small-en-v1.5", lastUserMsg)
		if err == nil && len(emb) > 0 {
			_ = s.semanticCache.Save(ctx, emb, lastUserMsg, resp, fingerprint)
		}
	}

	if cacheInfo != nil {
		cacheInfo.Cached = false
		cacheInfo.CacheType = "none"
	}

	return resp, nil
}

func (s *AIService) compactHistoryIfNeed(ctx context.Context, userID string, modelID string) error {
	threshold := getIntEnv("AI_COMPACTION_THRESHOLD", 20)

	session, err := s.repo.GetSession(ctx, userID)
	if err != nil || session == nil {
		return err
	}

	if len(session.Messages) <= threshold {
		return nil
	}

	keepCount := 4
	compactEnd := len(session.Messages) - keepCount
	compactMessages := session.Messages[:compactEnd]
	keepMessages := session.Messages[compactEnd:]

	var historyBuilder strings.Builder
	for _, msg := range compactMessages {
		historyBuilder.WriteString(fmt.Sprintf("%s: %s\n", msg.Role, msg.Content))
	}

	prompt := []ChatMessage{
		{
			Role:    "system",
			Content: "Summarize the key facts, preferences, goals, and decisions discussed in the following conversation history in under 3 sentences:",
		},
		{
			Role:    "user",
			Content: historyBuilder.String(),
		},
	}

	summary, err := s.provider.GenerateCompletion(ctx, modelID, prompt)
	if err != nil {
		return err
	}

	compactedMsg := ChatMessage{
		Role:      "system",
		Content:   "Summary of older conversation: " + summary,
		Timestamp: time.Now().Unix(),
	}

	newMessages := make([]ChatMessage, 0, len(keepMessages)+1)
	newMessages = append(newMessages, compactedMsg)
	newMessages = append(newMessages, keepMessages...)
	session.Messages = newMessages

	return s.repo.SaveSession(ctx, session)
}

func (s *AIService) classifyAndRoute(ctx context.Context, userMessage string, defaultModelID string) string {
	smallModel := os.Getenv("AI_SMALL_MODEL")
	if smallModel == "" {
		smallModel = "@cf/meta/llama-3-8b-instruct-awq"
	}
	largeModel := os.Getenv("AI_LARGE_MODEL")
	if largeModel == "" {
		largeModel = "@cf/google/gemma-3-12b-it"
	}

	lowerMsg := strings.ToLower(userMessage)

	if len(userMessage) > 150 {
		return largeModel
	}

	complexKeywords := []string{
		"code", "bug", "error", "explain", "analyze", "debug", "solve", "math", "reason", "why", "how",
		"compare", "implement", "architect", "refactor", "optimise", "optimize", "class", "function",
		"golang", "python", "javascript", "docker", "kubernetes", "database", "sql", "write a", "create a",
		"script", "test", "benchmark", "compile", "exception", "crash", "deploy", "pipeline", "hexagonal",
	}

	for _, kw := range complexKeywords {
		if strings.Contains(lowerMsg, kw) {
			return largeModel
		}
	}

	codeSigns := []string{"{", "}", "func", "def ", "class ", "import ", "package ", "var ", "const ", "let ", "const"}
	for _, sign := range codeSigns {
		if strings.Contains(userMessage, sign) {
			return largeModel
		}
	}

	if len(userMessage) < 25 {
		return smallModel
	}

	return largeModel
}

func (s *AIService) processFacts(userEmbedding []float32, facts []UserFact) []UserFact {
	if len(facts) == 0 {
		return nil
	}

	limit := getIntEnv("AI_MEMORY_LIMIT", 5)
	simWeight := getFloatEnv("AI_SIM_WEIGHT", 0.5)
	recencyWeight := getFloatEnv("AI_RECENCY_WEIGHT", 0.3)
	importanceWeight := getFloatEnv("AI_IMPORTANCE_WEIGHT", 0.2)
	lambda := getFloatEnv("AI_MMR_LAMBDA", 0.5)
	halfLifeDays := getFloatEnv("AI_RECENCY_HALF_LIFE_DAYS", 7.0)
	halfLifeSec := halfLifeDays * 86400.0

	type scoredFact struct {
		fact  UserFact
		score float64
	}

	var scored []scoredFact
	now := time.Now().Unix()

	for _, f := range facts {
		sim := 0.0
		if len(f.Embedding) > 0 && len(userEmbedding) > 0 {
			sim = cosineSimilarity(userEmbedding, f.Embedding)
		}

		age := float64(now - f.Timestamp)
		if age < 0 {
			age = 0
		}
		recency := math.Exp(-(age * 0.693147 / halfLifeSec))
		impNorm := float64(f.Importance) / 5.0

		combined := sim*simWeight + recency*recencyWeight + impNorm*importanceWeight
		scored = append(scored, scoredFact{fact: f, score: combined})
	}

	keep := make([]bool, len(scored))
	for i := range keep {
		keep[i] = true
	}

	for i := 0; i < len(scored); i++ {
		if !keep[i] {
			continue
		}
		for j := i + 1; j < len(scored); j++ {
			if !keep[j] {
				continue
			}
			if len(scored[i].fact.Embedding) > 0 && len(scored[j].fact.Embedding) > 0 {
				sim := cosineSimilarity(scored[i].fact.Embedding, scored[j].fact.Embedding)
				if sim > 0.85 {
					if scored[i].fact.Timestamp >= scored[j].fact.Timestamp {
						keep[j] = false
					} else {
						keep[i] = false
						break
					}
				}
			}
		}
	}

	var filteredScored []scoredFact
	for i, k := range keep {
		if k {
			filteredScored = append(filteredScored, scored[i])
		}
	}

	if len(filteredScored) == 0 {
		return nil
	}

	sort.Slice(filteredScored, func(i, j int) bool {
		return filteredScored[i].score > filteredScored[j].score
	})

	var selected []scoredFact
	selected = append(selected, filteredScored[0])
	candidates := filteredScored[1:]

	for len(selected) < limit && len(candidates) > 0 {
		bestIdx := -1
		bestMMR := -math.MaxFloat64

		for idx, cand := range candidates {
			maxSim := -1.0
			if len(cand.fact.Embedding) > 0 {
				for _, sel := range selected {
					if len(sel.fact.Embedding) > 0 {
						sim := cosineSimilarity(cand.fact.Embedding, sel.fact.Embedding)
						if sim > maxSim {
							maxSim = sim
						}
					}
				}
			}
			if maxSim == -1.0 {
				maxSim = 0.0
			}

			mmrVal := lambda*cand.score - (1.0-lambda)*maxSim
			if mmrVal > bestMMR {
				bestMMR = mmrVal
				bestIdx = idx
			}
		}

		if bestIdx == -1 {
			break
		}
		selected = append(selected, candidates[bestIdx])
		candidates = append(candidates[:bestIdx], candidates[bestIdx+1:]...)
	}

	var finalFacts []UserFact
	for _, sf := range selected {
		finalFacts = append(finalFacts, sf.fact)
	}
	return finalFacts
}

func (s *AIService) extractAndSaveFacts(ctx context.Context, userID string, userMsg string, assistantMsg string, embeddingModel string) {
	smallModel := os.Getenv("AI_SMALL_MODEL")
	if smallModel == "" {
		smallModel = "@cf/meta/llama-3-8b-instruct-awq"
	}

	promptText := fmt.Sprintf("Analyze the following dialogue turn between a user and an assistant. "+
		"Identify and extract any key user facts, preferences, or goals. For each, assign an importance score (1 to 5, where 5 is critical/long-term and 1 is transient/trivial). "+
		"Format the response strictly as a JSON array of objects with keys 'fact' and 'importance'. If no relevant facts exist, output an empty JSON array [].\n\n"+
		"Dialogue:\nUser: %s\nAssistant: %s", userMsg, assistantMsg)

	prompt := []ChatMessage{
		{
			Role:    "system",
			Content: "You are a fact extraction assistant. Output ONLY valid JSON array and nothing else.",
		},
		{
			Role:    "user",
			Content: promptText,
		},
	}

	res, err := s.provider.GenerateCompletion(ctx, smallModel, prompt)
	if err != nil {
		return
	}

	res = strings.TrimSpace(res)
	if strings.HasPrefix(res, "```") {
		res = strings.TrimPrefix(res, "```json")
		res = strings.TrimPrefix(res, "```")
		res = strings.TrimSuffix(res, "```")
		res = strings.TrimSpace(res)
	}

	var extracted []struct {
		Fact       string `json:"fact"`
		Importance int    `json:"importance"`
	}

	if err := json.Unmarshal([]byte(res), &extracted); err != nil {
		return
	}

	if len(extracted) == 0 {
		return
	}

	session, _ := s.repo.GetSession(ctx, userID)

	for _, item := range extracted {
		factText := strings.TrimSpace(item.Fact)
		if factText == "" {
			continue
		}
		importance := item.Importance
		if importance < 1 {
			importance = 1
		} else if importance > 5 {
			importance = 5
		}

		var emb []float32
		if embeddingModel != "" {
			emb, _ = s.provider.GenerateEmbedding(ctx, embeddingModel, factText)
		}

		factObj := UserFact{
			Fact:       factText,
			Importance: importance,
			Timestamp:  time.Now().Unix(),
			Embedding:  emb,
		}

		if s.vectorRepo != nil && len(emb) > 0 {
			factID := generateUUID()
			payload := map[string]interface{}{
				"user_id":    userID,
				"fact":       factText,
				"importance": float64(importance),
				"timestamp":  float64(factObj.Timestamp),
				"embedding":  emb,
			}
			_ = s.vectorRepo.Upsert(ctx, factID, emb, payload)
		} else if session != nil {
			session.Facts = append(session.Facts, factObj)
		}
	}

	if session != nil {
		_ = s.repo.SaveSession(ctx, session)
	}
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

	var (
		userEmbedding []float32
		session       *ChatSession
		sessionErr    error
		embedErr      error
	)

	var wg sync.WaitGroup
	wg.Add(2)

	go func() {
		defer wg.Done()
		if embeddingModel != "" {
			userEmbedding, embedErr = s.provider.GenerateEmbedding(ctx, embeddingModel, userMessage)
		}
	}()

	go func() {
		defer wg.Done()
		session, sessionErr = s.repo.GetSession(ctx, userID)
	}()

	wg.Wait()

	if sessionErr != nil {
		return "", nil, sessionErr
	}
	_ = embedErr

	if session == nil {
		session = &ChatSession{
			UserID:         userID,
			Messages:       []ChatMessage{},
			LastAccessedAt: time.Now(),
		}
	}

	session.LastAccessedAt = time.Now()

	var retrievedFacts []UserFact

	if s.vectorRepo != nil && len(userEmbedding) > 0 {
		matches, err := s.vectorRepo.Search(ctx, userID, userEmbedding, 15)
		if err == nil && len(matches) > 0 {
			for _, m := range matches {
				fact, _ := m.Payload["fact"].(string)
				var importance int
				if val, ok := m.Payload["importance"].(float64); ok {
					importance = int(val)
				} else if val, ok := m.Payload["importance"].(int64); ok {
					importance = int(val)
				}
				var ts int64
				if val, ok := m.Payload["timestamp"].(float64); ok {
					ts = int64(val)
				} else if val, ok := m.Payload["timestamp"].(int64); ok {
					ts = val
				}
				var emb []float32
				if val, ok := m.Payload["embedding"].([]interface{}); ok {
					emb = make([]float32, len(val))
					for idx, v := range val {
						if vf, ok := v.(float64); ok {
							emb[idx] = float32(vf)
						}
					}
				}
				retrievedFacts = append(retrievedFacts, UserFact{
					Fact:       fact,
					Importance: importance,
					Timestamp:  ts,
					Embedding:  emb,
				})
			}
		}
	} else if len(userEmbedding) > 0 && session != nil && len(session.Facts) > 0 {
		retrievedFacts = session.Facts
	}

	processedFacts := s.processFacts(userEmbedding, retrievedFacts)

	var apiMessages []ChatMessage

	if len(processedFacts) > 0 {
		var contextBuilder strings.Builder
		contextBuilder.WriteString("User Profile & Facts (reconciled):\n")
		for _, f := range processedFacts {
			contextBuilder.WriteString(fmt.Sprintf("- %s\n", f.Fact))
		}
		contextBuilder.WriteString("\nInstructions: Use the above User Profile & Facts to tailor your response. If the current conversation contradicts these past facts, prioritize the active conversation, but acknowledge or gently reconcile the change if necessary.")
		apiMessages = append(apiMessages, ChatMessage{
			Role:      "system",
			Content:   contextBuilder.String(),
			Timestamp: time.Now().Unix(),
		})
	}

	for _, msg := range session.Messages {
		apiMessages = append(apiMessages, ChatMessage{
			Role:      msg.Role,
			Content:   msg.Content,
			Timestamp: msg.Timestamp,
		})
	}

	apiMessages = append(apiMessages, ChatMessage{
		Role:      "user",
		Content:   userMessage,
		Timestamp: time.Now().Unix(),
	})

	cacheInfo := GetCacheInfo(ctx)
	var cacheKey string
	var cachedVal string
	var cacheFound bool

	if s.cache != nil {
		cacheKey = "stateful:" + generateCacheKey(modelID, apiMessages)
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

	fingerprint := generatePromptFingerprint(modelID, apiMessages)

	if !cacheFound && s.semanticCache != nil && len(userEmbedding) > 0 {
		threshold := float32(getFloatEnv("AI_SEMANTIC_CACHE_THRESHOLD", 0.90))
		val, err := s.semanticCache.GetSimilar(ctx, userEmbedding, threshold, fingerprint)
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
		routedModel := s.classifyAndRoute(ctx, userMessage, modelID)
		comp, err := s.provider.GenerateCompletion(ctx, routedModel, apiMessages)
		if err != nil {
			return "", nil, err
		}
		completion = comp

		if s.cache != nil && cacheKey != "" {
			_ = s.cache.Set(ctx, cacheKey, completion)
		}
		if s.semanticCache != nil && len(userEmbedding) > 0 {
			_ = s.semanticCache.Save(ctx, userEmbedding, userMessage, completion, fingerprint)
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
		Timestamp: time.Now().Unix(),
	}

	newAssistantMsg := ChatMessage{
		Role:      "assistant",
		Content:   completion,
		Timestamp: time.Now().Unix(),
	}

	session.Messages = append(session.Messages, newUserMsg, newAssistantMsg)

	if err := s.repo.SaveSession(ctx, session); err != nil {
		return "", nil, err
	}

	go func() {
		bgCtx, cancel := context.WithTimeout(context.Background(), 60*time.Second)
		defer cancel()
		_ = s.compactHistoryIfNeed(bgCtx, userID, modelID)
		s.extractAndSaveFacts(bgCtx, userID, userMessage, completion, embeddingModel)
	}()

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
