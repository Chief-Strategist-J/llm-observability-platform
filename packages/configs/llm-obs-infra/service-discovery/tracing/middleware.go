package tracing

import (
	"fmt"
	"net/http"
	"time"
)

type statusResponseWriter struct {
	http.ResponseWriter
	statusCode int
}

func (w *statusResponseWriter) WriteHeader(code int) {
	w.statusCode = code
	w.ResponseWriter.WriteHeader(code)
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
			Attributes: make(map[string]string),
		}

		span.SetAttribute("http.method", req.Method)
		span.SetAttribute("http.path", req.URL.Path)
		span.SetAttribute("http.client_ip", req.RemoteAddr)

		w.Header().Set("traceparent", span.TraceparentHeader())

		sw := &statusResponseWriter{ResponseWriter: w, statusCode: http.StatusOK}
		ctx := req.Context()
		ctx = contextWithValue(ctx, SpanContextKey, span)

		next.ServeHTTP(sw, req.WithContext(ctx))

		span.SetAttribute("http.status_code", fmt.Sprintf("%d", sw.statusCode))
		span.End()
	})
}

func contextWithValue(ctx context.Context, key interface{}, val interface{}) context.Context {
	return context.WithValue(ctx, key, val)
}
