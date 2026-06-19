package tracep

import (
	"net/http"
	"net/http/httptest"
	"testing"
	"time"
)

func TestTracerFacadeFlow(t *testing.T) {
	// Create mock OTLP server
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
		_, _ = w.Write([]byte(`{}`))
	}))
	defer server.Close()

	tracer, err := New(server.URL, "secret-token", "test-app")
	if err != nil {
		t.Fatalf("failed to create tracer: %v", err)
	}
	defer tracer.Close()

	tid := tracer.Start("checkout-flow")
	if tid == "" {
		t.Error("expected non-empty trace ID (tid)")
	}

	tracer.Trace(tid, "OrderService", "createOrder", "start", "order received")
	tracer.Trace(tid, "PaymentService", "charge", "start", "charging card", WithParent("createOrder"))
	tracer.Trace(tid, "PaymentService", "charge", "error", "card declined", WithLevel("error"))
	tracer.Trace(tid, "OrderService", "createOrder", "error", "payment failed", WithLevel("error"))

	tracer.End(tid, "error")

	// Allow exporter some time to flush
	time.Sleep(100 * time.Millisecond)
}
