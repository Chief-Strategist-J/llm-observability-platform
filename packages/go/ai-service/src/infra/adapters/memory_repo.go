package adapters

import (
	"context"
	"sync"
	"time"

	aiorchestrator "github.com/llm-observability/platform/packages/go/ai-service/src/features/ai_orchestrator"
)

type MemorySessionRepository struct {
	mu       sync.RWMutex
	sessions map[string]*aiorchestrator.ChatSession
	ttl      time.Duration
	stopChan chan struct{}
}

func NewMemorySessionRepository(cleanupInterval time.Duration) *MemorySessionRepository {
	r := &MemorySessionRepository{
		sessions: make(map[string]*aiorchestrator.ChatSession),
		ttl:      15 * time.Minute,
		stopChan: make(chan struct{}),
	}
	go r.startCleanupLoop(cleanupInterval)
	return r
}

func (r *MemorySessionRepository) Stop() {
	close(r.stopChan)
}

func (r *MemorySessionRepository) GetSession(ctx context.Context, userID string) (*aiorchestrator.ChatSession, error) {
	r.mu.RLock()
	defer r.mu.RUnlock()

	session, exists := r.sessions[userID]
	if !exists {
		return nil, nil
	}

	if time.Since(session.LastAccessedAt) > r.ttl {
		return nil, nil
	}

	return session, nil
}

func (r *MemorySessionRepository) SaveSession(ctx context.Context, session *aiorchestrator.ChatSession) error {
	r.mu.Lock()
	defer r.mu.Unlock()

	r.sessions[session.UserID] = session
	return nil
}

func (r *MemorySessionRepository) DeleteSession(ctx context.Context, userID string) error {
	r.mu.Lock()
	defer r.mu.Unlock()

	delete(r.sessions, userID)
	return nil
}

func (r *MemorySessionRepository) startCleanupLoop(interval time.Duration) {
	ticker := time.NewTicker(interval)
	defer ticker.Stop()

	for {
		select {
		case <-ticker.C:
			r.mu.Lock()
			now := time.Now()
			for id, sess := range r.sessions {
				if now.Sub(sess.LastAccessedAt) > r.ttl {
					delete(r.sessions, id)
				}
			}
			r.mu.Unlock()
		case <-r.stopChan:
			return
		}
	}
}
