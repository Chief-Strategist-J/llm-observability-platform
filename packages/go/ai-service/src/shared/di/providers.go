package di

import (
	"net/http"
	"os"
	"time"

	v1 "github.com/llm-observability/platform/packages/go/ai-service/src/api/rest/v1"
	"github.com/llm-observability/platform/packages/go/ai-service/src/api/rest/v1/handlers"
	aiorchestrator "github.com/llm-observability/platform/packages/go/ai-service/src/features/ai_orchestrator"
	"github.com/llm-observability/platform/packages/go/ai-service/src/infra/adapters"
)

type Container struct {
	Router     http.Handler
	MemoryRepo *adapters.MemorySessionRepository
}

func BuildContainer() *Container {
	accountID := os.Getenv("CF_ACCOUNT_ID")
	apiToken := os.Getenv("CF_API_TOKEN")

	provider := adapters.NewCloudflareAdapter(accountID, apiToken)
	repo := adapters.NewMemorySessionRepository(1 * time.Minute)

	orch := aiorchestrator.New(provider, repo)
	h := handlers.NewAIHandlers(orch)
	router := v1.NewRouter(h)

	return &Container{
		Router:     router,
		MemoryRepo: repo,
	}
}
