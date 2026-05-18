package handlers

import (
	"encoding/json"
	"net/http"
	"os"
	"strings"

	aiorchestrator "github.com/llm-observability/platform/packages/go/ai-service/src/features/ai_orchestrator"
	"go.opentelemetry.io/otel"
	"go.opentelemetry.io/otel/attribute"
	"go.opentelemetry.io/otel/codes"
)

type AIHandlers struct {
	orch aiorchestrator.Orchestrator
}

func NewAIHandlers(orch aiorchestrator.Orchestrator) *AIHandlers {
	return &AIHandlers{orch: orch}
}

type chatRequest struct {
	Model    string                        `json:"model"`
	Messages []aiorchestrator.ChatMessage `json:"messages"`
}

type chatResponse struct {
	Response string `json:"response"`
}

type persistentChatRequest struct {
	UserID         string `json:"user_id"`
	Message        string `json:"message"`
	Model          string `json:"model"`
	EmbeddingModel string `json:"embedding_model"`
}

type persistentChatResponse struct {
	Response string                        `json:"response"`
	History  []aiorchestrator.ChatMessage `json:"history"`
}

func (h *AIHandlers) ListModels(w http.ResponseWriter, r *http.Request) {
	ctx := r.Context()
	tr := otel.Tracer("ai-service")
	ctx, span := tr.Start(ctx, "ListModelsHandler")
	defer span.End()

	span.SetAttributes(
		attribute.String("http.method", r.Method),
		attribute.String("http.route", r.URL.Path),
		attribute.String("feature.name", "ai_orchestrator"),
		attribute.String("api.version", "v1"),
	)

	models, err := h.orch.ListModels(ctx)
	if err != nil {
		span.RecordError(err)
		span.SetStatus(codes.Error, err.Error())
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(models)
}

func (h *AIHandlers) Chat(w http.ResponseWriter, r *http.Request) {
	ctx := r.Context()
	tr := otel.Tracer("ai-service")
	ctx, span := tr.Start(ctx, "ChatHandler")
	defer span.End()

	span.SetAttributes(
		attribute.String("http.method", r.Method),
		attribute.String("http.route", r.URL.Path),
		attribute.String("feature.name", "ai_orchestrator"),
		attribute.String("api.version", "v1"),
	)

	if r.Method != http.MethodPost {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	var req chatRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		span.RecordError(err)
		span.SetStatus(codes.Error, err.Error())
		http.Error(w, "Invalid request body", http.StatusBadRequest)
		return
	}

	if req.Model == "" {
		req.Model = os.Getenv("AI_DEFAULT_MODEL")
		if req.Model == "" {
			req.Model = "@cf/meta/llama-3.1-8b-instruct"
		}
	}

	span.SetAttributes(attribute.String("ai.model", req.Model))

	res, err := h.orch.Chat(ctx, req.Model, req.Messages)
	if err != nil {
		span.RecordError(err)
		span.SetStatus(codes.Error, err.Error())
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(chatResponse{Response: res})
}

func (h *AIHandlers) PersistentChat(w http.ResponseWriter, r *http.Request) {
	ctx := r.Context()
	tr := otel.Tracer("ai-service")
	ctx, span := tr.Start(ctx, "PersistentChatHandler")
	defer span.End()

	span.SetAttributes(
		attribute.String("http.method", r.Method),
		attribute.String("http.route", r.URL.Path),
		attribute.String("feature.name", "ai_orchestrator"),
		attribute.String("api.version", "v1"),
	)

	if r.Method != http.MethodPost {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	var req persistentChatRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		span.RecordError(err)
		span.SetStatus(codes.Error, err.Error())
		http.Error(w, "Invalid request body", http.StatusBadRequest)
		return
	}

	if strings.TrimSpace(req.UserID) == "" {
		http.Error(w, "user_id is required", http.StatusBadRequest)
		return
	}

	if strings.TrimSpace(req.Message) == "" {
		http.Error(w, "message is required", http.StatusBadRequest)
		return
	}

	if req.Model == "" {
		req.Model = os.Getenv("AI_DEFAULT_MODEL")
		if req.Model == "" {
			req.Model = "@cf/meta/llama-3.1-8b-instruct"
		}
	}

	if req.EmbeddingModel == "" {
		req.EmbeddingModel = os.Getenv("CF_EMBEDDING_MODEL")
		if req.EmbeddingModel == "" {
			req.EmbeddingModel = "@cf/baai/bge-small-en-v1.5"
		}
	}

	span.SetAttributes(
		attribute.String("user.id", req.UserID),
		attribute.String("ai.model", req.Model),
		attribute.String("ai.embedding_model", req.EmbeddingModel),
	)

	res, history, err := h.orch.PersistentChat(ctx, req.UserID, req.Message, req.Model, req.EmbeddingModel)
	if err != nil {
		span.RecordError(err)
		span.SetStatus(codes.Error, err.Error())
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(persistentChatResponse{
		Response: res,
		History:  history,
	})
}
