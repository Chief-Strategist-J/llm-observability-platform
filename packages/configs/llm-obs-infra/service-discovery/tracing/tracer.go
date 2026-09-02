package tracing

import (
	"context"
	"crypto/rand"
	"encoding/hex"
	"fmt"
	"log"
	"net/http"
	"strings"
	"sync"
	"time"
)

type contextKey string

const (
	SpanContextKey contextKey = "sd_span_context"
)

type Span struct {
	TraceID    string
	SpanID     string
	ParentID   string
	Name       string
	StartTime  time.Time
	Attributes map[string]string
	mu         sync.Mutex
}

func generateID(byteLen int) string {
	b := make([]byte, byteLen)
	_, _ = rand.Read(b)
	return hex.EncodeToString(b)
}

func NewTraceID() string {
	return generateID(16)
}

func NewSpanID() string {
	return generateID(8)
}

func StartSpan(ctx context.Context, name string) (context.Context, *Span) {
	var traceID, parentID string
	if parent, ok := SpanFromContext(ctx); ok && parent != nil {
		traceID = parent.TraceID
		parentID = parent.SpanID
	} else {
		traceID = NewTraceID()
	}

	span := &Span{
		TraceID:    traceID,
		SpanID:     NewSpanID(),
		ParentID:   parentID,
		Name:       name,
		StartTime:  time.Time{},
		Attributes: make(map[string]string),
	}

	newCtx := context.WithValue(ctx, SpanContextKey, span)
	return newCtx, span
}

func SpanFromContext(ctx context.Context) (*Span, bool) {
	if ctx == nil {
		return nil, false
	}
	span, ok := ctx.Value(SpanContextKey).(*Span)
	return span, ok
}

func (s *Span) SetAttribute(key, value string) {
	if s == nil {
		return
	}
	s.mu.Lock()
	defer s.mu.Unlock()
	s.Attributes[key] = value
}

func (s *Span) End() {
	if s == nil {
		return
	}
	duration := time.Since(s.StartTime)
	log.Printf("[tracer] span=%q trace_id=%s span_id=%s parent_id=%s duration=%s attrs=%v",
		s.Name, s.TraceID, s.SpanID, s.ParentID, duration, s.Attributes)
}

func (s *Span) TraceparentHeader() string {
	if s == nil {
		return ""
	}
	return fmt.Sprintf("00-%s-%s-01", s.TraceID, s.SpanID)
}

func ParseTraceparent(header string) (traceID, spanID string, ok bool) {
	parts := strings.Split(header, "-")
	if len(parts) >= 3 && parts[0] == "00" && len(parts[1]) == 32 && len(parts[2]) == 16 {
		return parts[1], parts[2], true
	}
	return "", "", false
}

func InjectHTTPHeaders(ctx context.Context, req *http.Request) {
	if span, ok := SpanFromContext(ctx); ok && span != nil {
		req.Header.Set("traceparent", span.TraceparentHeader())
	}
}

func ExtractHTTPHeaders(req *http.Request) (traceID, parentID string) {
	header := req.Header.Get("traceparent")
	if header != "" {
		if tID, sID, ok := ParseTraceparent(header); ok {
			return tID, sID
		}
	}
	return NewTraceID(), ""
}
