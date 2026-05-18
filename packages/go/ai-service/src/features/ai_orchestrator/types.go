package aiorchestrator

import "time"

type ModelInfo struct {
	ID          string `json:"id"`
	Name        string `json:"name"`
	Description string `json:"description"`
	Provider    string `json:"provider"`
}

type ChatMessage struct {
	Role      string    `json:"role"`
	Content   string    `json:"content"`
	Embedding []float32 `json:"-"`
}

type ChatSession struct {
	UserID         string        `json:"user_id"`
	Messages       []ChatMessage `json:"messages"`
	LastAccessedAt time.Time     `json:"last_accessed_at"`
}
