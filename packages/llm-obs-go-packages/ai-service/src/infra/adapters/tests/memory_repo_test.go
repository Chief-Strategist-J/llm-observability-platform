package tests

import (
	"context"
	"testing"
	"time"

	aiorchestrator "github.com/llm-observability/platform/packages/go/ai-service/src/features/ai_orchestrator"
	"github.com/llm-observability/platform/packages/go/ai-service/src/infra/adapters"
)

func TestMemoryRepoCRUD(t *testing.T) {
	repo := adapters.NewMemorySessionRepository(10 * time.Minute)
	defer repo.Stop()

	ctx := context.Background()
	sess, err := repo.GetSession(ctx, "user-1")
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if sess != nil {
		t.Errorf("expected nil session, got %v", sess)
	}

	newSess := &aiorchestrator.ChatSession{
		UserID:         "user-1",
		Messages:       []aiorchestrator.ChatMessage{},
		LastAccessedAt: time.Now(),
	}

	err = repo.SaveSession(ctx, newSess)
	if err != nil {
		t.Fatalf("unexpected save error: %v", err)
	}

	sess, err = repo.GetSession(ctx, "user-1")
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if sess == nil || sess.UserID != "user-1" {
		t.Errorf("unexpected session returned: %v", sess)
	}

	err = repo.DeleteSession(ctx, "user-1")
	if err != nil {
		t.Fatalf("unexpected delete error: %v", err)
	}

	sess, err = repo.GetSession(ctx, "user-1")
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if sess != nil {
		t.Errorf("expected nil session after deletion, got %v", sess)
	}
}

func TestMemoryRepoTTL(t *testing.T) {
	repo := adapters.NewMemorySessionRepository(10 * time.Millisecond)
	defer repo.Stop()

	ctx := context.Background()
	newSess := &aiorchestrator.ChatSession{
		UserID:         "user-2",
		Messages:       []aiorchestrator.ChatMessage{},
		LastAccessedAt: time.Now().Add(-20 * time.Minute),
	}

	err := repo.SaveSession(ctx, newSess)
	if err != nil {
		t.Fatalf("unexpected save error: %v", err)
	}

	time.Sleep(30 * time.Millisecond)

	sess, err := repo.GetSession(ctx, "user-2")
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if sess != nil {
		t.Errorf("expected session to be pruned or expired, got %v", sess)
	}
}
