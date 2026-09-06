package v1

import (
	"net/http"

	"github.com/llm-observability/platform/packages/go/ai-service/src/api/rest/v1/handlers"
)

func NewRouter(h *handlers.AIHandlers) http.Handler {
	mux := http.NewServeMux()
	mux.HandleFunc("/api/v1/models", h.ListModels)
	mux.HandleFunc("/api/v1/chat", h.Chat)
	mux.HandleFunc("/api/v1/chat/persistent", h.PersistentChat)
	return mux
}
