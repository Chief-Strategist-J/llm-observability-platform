package di

import (
	"context"
	"net/http"
	"os"
	"strconv"
	"time"

	v1 "github.com/llm-observability/platform/packages/go/ai-service/src/api/rest/v1"
	"github.com/llm-observability/platform/packages/go/ai-service/src/api/rest/v1/handlers"
	aiorchestrator "github.com/llm-observability/platform/packages/go/ai-service/src/features/ai_orchestrator"
	"github.com/llm-observability/platform/packages/go/ai-service/src/infra/adapters"
)

type Container struct {
	Router      http.Handler
	MemoryRepo  *adapters.MemorySessionRepository
	MemoryCache *adapters.MemoryResponseCache
}

func BuildContainer() *Container {
	accountID := os.Getenv("CF_ACCOUNT_ID")
	apiToken := os.Getenv("CF_API_TOKEN")

	provider := adapters.NewCloudflareAdapter(accountID, apiToken)
	repo := adapters.NewMemorySessionRepository(1 * time.Minute)
	memoryCache := adapters.NewMemoryResponseCache(5*time.Minute, 1*time.Minute)

	orch := aiorchestrator.New(provider, repo)

	if service, ok := orch.(*aiorchestrator.AIService); ok {
		service.SetResponseCache(memoryCache)
	}

	if qdrantURL := os.Getenv("QDRANT_URL"); qdrantURL != "" {
		qdrantApiKey := os.Getenv("QDRANT_API_KEY")
		qdrantCollection := os.Getenv("QDRANT_COLLECTION")

		vectorSize := 384
		if sizeStr := os.Getenv("QDRANT_VECTOR_SIZE"); sizeStr != "" {
			if parsedSize, err := strconv.Atoi(sizeStr); err == nil {
				vectorSize = parsedSize
			}
		}

		distance := "Cosine"
		if distStr := os.Getenv("QDRANT_DISTANCE"); distStr != "" {
			distance = distStr
		}

		qdrantRepo := adapters.NewQdrantRepository(qdrantURL, qdrantApiKey, qdrantCollection)

		ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
		defer cancel()
		_ = qdrantRepo.CreateCollectionIfNotExist(ctx, vectorSize, distance)

		if service, ok := orch.(*aiorchestrator.AIService); ok {
			service.SetVectorRepository(qdrantRepo)
		}

		semanticCollection := os.Getenv("QDRANT_SEMANTIC_CACHE_COLLECTION")
		if semanticCollection == "" {
			semanticCollection = "semantic_cache"
		}
		qdrantCache := adapters.NewQdrantSemanticCache(qdrantURL, qdrantApiKey, semanticCollection)
		_ = qdrantCache.CreateCollectionIfNotExist(ctx, 384, distance)

		if service, ok := orch.(*aiorchestrator.AIService); ok {
			service.SetSemanticCache(qdrantCache)
		}
	}

	h := handlers.NewAIHandlers(orch)
	router := v1.NewRouter(h)

	return &Container{
		Router:      router,
		MemoryRepo:  repo,
		MemoryCache: memoryCache,
	}
}
