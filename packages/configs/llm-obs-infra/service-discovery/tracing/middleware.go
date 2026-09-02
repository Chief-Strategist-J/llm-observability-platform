package tracing

import (
	"context"
	"crypto/rand"
	"encoding/hex"
	"fmt"
	"net/http"
	"time"
)

type RequestContext struct {
	Traceparent    string
	Tracestate     string
	RequestId      string
	CorrelationId  string
	CausationId    string
	IdempotencyKey string
	TenantId       string
	ClientId       string
	UserId         string
	StartTime      time.Time
}

type reqContextKey string

const ReqContextKey reqContextKey = "requestContext"

type statusResponseWriter struct {
	http.ResponseWriter
	statusCode int
}

func (w *statusResponseWriter) WriteHeader(code int) {
	w.statusCode = code
	w.ResponseWriter.WriteHeader(code)
}

func generateID(prefix string) string {
	b := make([]byte, 6)
	_, _ = rand.Read(b)
	return fmt.Sprintf("%s-%d-%s", prefix, time.Now().UnixMilli(), hex.EncodeToString(b))
}

func Middleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, req *http.Request) {
		start := time.Now()
		traceID, parentID := ExtractHTTPHeaders(req)

		span := &Span{
			TraceID:    traceID,
			SpanID:     NewSpanID(),
			ParentID:   parentID,
			Name:       fmt.Sprintf("HTTP %s %s", req.Method, req.URL.Path),
			StartTime:  start,
			Status:     "OK",
			Attributes: make(map[string]string),
		}

		tracestate := req.Header.Get("tracestate")

		reqID := req.Header.Get("x-request-id")
		if reqID == "" {
			reqID = generateID("req")
		}

		corrID := req.Header.Get("x-correlation-id")
		if corrID == "" {
			corrID = reqID
		}

		causID := req.Header.Get("x-causation-id")
		if causID == "" {
			causID = reqID
		}

		idemKey := req.Header.Get("x-idempotency-key")
		if idemKey == "" {
			idemKey = reqID
		}

		tenantID := req.Header.Get("x-tenant-id")
		if tenantID == "" {
			tenantID = "tenant-default"
		}

		clientID := req.Header.Get("x-client-id")

		userID := req.Header.Get("x-user-id")
		if userID == "" {
			userID = "anonymous"
		}

		reqCtx := RequestContext{
			Traceparent:    span.TraceparentHeader(),
			Tracestate:     tracestate,
			RequestId:      reqID,
			CorrelationId:  corrID,
			CausationId:    causID,
			IdempotencyKey: idemKey,
			TenantId:       tenantID,
			ClientId:       clientID,
			UserId:         userID,
			StartTime:      start,
		}

		span.SetAttribute("http.method", req.Method)
		span.SetAttribute("http.path", req.URL.Path)
		span.SetAttribute("http.client_ip", req.RemoteAddr)
		span.SetAttribute("x-request-id", reqID)
		span.SetAttribute("x-correlation-id", corrID)
		span.SetAttribute("x-causation-id", causID)
		span.SetAttribute("x-tenant-id", tenantID)
		span.SetAttribute("x-user-id", userID)

		// Inject outbound header requirements per specification
		w.Header().Set("traceparent", reqCtx.Traceparent)
		if tracestate != "" {
			w.Header().Set("tracestate", tracestate)
		}
		w.Header().Set("x-request-id", reqID)
		w.Header().Set("x-correlation-id", corrID)
		w.Header().Set("x-causation-id", causID)
		w.Header().Set("x-tenant-id", tenantID)
		if clientID != "" {
			w.Header().Set("x-client-id", clientID)
		}
		w.Header().Set("x-user-id", userID)

		sw := &statusResponseWriter{ResponseWriter: w, statusCode: http.StatusOK}
		ctx := req.Context()
		ctx = context.WithValue(ctx, SpanContextKey, span)
		ctx = context.WithValue(ctx, ReqContextKey, reqCtx)

		next.ServeHTTP(sw, req.WithContext(ctx))

		span.SetAttribute("http.status_code", fmt.Sprintf("%d", sw.statusCode))
		if sw.statusCode >= 400 {
			span.SetStatus("ERROR")
		} else {
			span.SetStatus("OK")
		}
		span.End()
	})
}

func GetRequestContext(ctx context.Context) RequestContext {
	if val, ok := ctx.Value(ReqContextKey).(RequestContext); ok {
		return val
	}
	start := time.Now()
	id := generateID("req")
	return RequestContext{
		Traceparent:    fmt.Sprintf("00-%s-%s-01", NewTraceID(), NewSpanID()),
		RequestId:      id,
		CorrelationId:  id,
		CausationId:    id,
		IdempotencyKey: id,
		TenantId:       "tenant-default",
		UserId:         "anonymous",
		StartTime:      start,
	}
}
