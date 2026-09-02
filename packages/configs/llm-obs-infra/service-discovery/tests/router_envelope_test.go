package tests

import (
	"bytes"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"

	"github.com/llm-observability/platform/packages/configs/llm-obs-infra/service-discovery/discovery"
	"github.com/llm-observability/platform/packages/configs/llm-obs-infra/service-discovery/models"
	"github.com/llm-observability/platform/packages/configs/llm-obs-infra/service-discovery/registry"
	"github.com/llm-observability/platform/packages/configs/llm-obs-infra/service-discovery/server"
)

func setupTestRouter() *server.Router {
	reg := registry.NewRegistry(registry.DefaultInstanceDefaults)
	disc := discovery.NewDiscovery(reg)
	return server.NewRouter(reg, disc, models.SecurityConfig{EnforceRFC1918: false})
}

func TestStandardSuccessEnvelope(t *testing.T) {
	r := setupTestRouter()

	payload := map[string]interface{}{
		"name":     "test-service",
		"host":     "test-service-container",
		"port":     9000,
		"protocol": "http",
	}
	body, _ := json.Marshal(payload)

	req := httptest.NewRequest(http.MethodPost, "/v1/register", bytes.NewBuffer(body))
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("x-request-id", "req-test-12345")
	req.Header.Set("x-correlation-id", "corr-test-67890")

	rec := httptest.NewRecorder()
	r.ServeHTTP(rec, req)

	if rec.Code != http.StatusCreated {
		t.Fatalf("expected status 201, got %d: %s", rec.Code, rec.Body.String())
	}

	if rec.Header().Get("x-request-id") != "req-test-12345" {
		t.Errorf("expected x-request-id response header 'req-test-12345', got '%s'", rec.Header().Get("x-request-id"))
	}
	if rec.Header().Get("x-correlation-id") != "corr-test-67890" {
		t.Errorf("expected x-correlation-id response header 'corr-test-67890', got '%s'", rec.Header().Get("x-correlation-id"))
	}

	var envelope models.ApiResponse[models.ServiceInstance]
	if err := json.Unmarshal(rec.Body.Bytes(), &envelope); err != nil {
		t.Fatalf("failed to parse ApiResponse envelope: %v", err)
	}

	if !envelope.Success {
		t.Errorf("expected success: true, got false")
	}
	if envelope.StatusCode != 201 {
		t.Errorf("expected statusCode 201, got %d", envelope.StatusCode)
	}
	if envelope.Data.Name != "test-service" {
		t.Errorf("expected data.name 'test-service', got '%s'", envelope.Data.Name)
	}
	if envelope.Meta.RequestId != "req-test-12345" {
		t.Errorf("expected meta.requestId 'req-test-12345', got '%s'", envelope.Meta.RequestId)
	}
}

func TestStandardValidationErrorEnvelope(t *testing.T) {
	r := setupTestRouter()

	// Missing mandatory 'host' and invalid 'port'
	payload := map[string]interface{}{
		"name":     "invalid-service",
		"port":     -1,
		"protocol": "http",
	}
	body, _ := json.Marshal(payload)

	req := httptest.NewRequest(http.MethodPost, "/v1/register", bytes.NewBuffer(body))
	req.Header.Set("Content-Type", "application/json")

	rec := httptest.NewRecorder()
	r.ServeHTTP(rec, req)

	if rec.Code != http.StatusBadRequest {
		t.Fatalf("expected status 400, got %d", rec.Code)
	}

	var errEnvelope models.ApiErrorResponse
	if err := json.Unmarshal(rec.Body.Bytes(), &errEnvelope); err != nil {
		t.Fatalf("failed to parse ApiErrorResponse envelope: %v", err)
	}

	if errEnvelope.Success {
		t.Errorf("expected success: false, got true")
	}
	if errEnvelope.StatusCode != 400 {
		t.Errorf("expected statusCode 400, got %d", errEnvelope.StatusCode)
	}
	if errEnvelope.Error.Code != models.ErrCodeValidationFailed {
		t.Errorf("expected code '%s', got '%s'", models.ErrCodeValidationFailed, errEnvelope.Error.Code)
	}
	if len(errEnvelope.Error.Details) < 2 {
		t.Errorf("expected at least 2 validation error details, got %d", len(errEnvelope.Error.Details))
	}
}

func TestNotFoundErrorEnvelope(t *testing.T) {
	r := setupTestRouter()

	payload := map[string]string{
		"name":       "non-existent",
		"instanceId": "missing-id",
	}
	body, _ := json.Marshal(payload)

	req := httptest.NewRequest(http.MethodPost, "/v1/heartbeat", bytes.NewBuffer(body))
	req.Header.Set("Content-Type", "application/json")

	rec := httptest.NewRecorder()
	r.ServeHTTP(rec, req)

	if rec.Code != http.StatusNotFound {
		t.Fatalf("expected status 404, got %d", rec.Code)
	}

	var errEnvelope models.ApiErrorResponse
	if err := json.Unmarshal(rec.Body.Bytes(), &errEnvelope); err != nil {
		t.Fatalf("failed to parse ApiErrorResponse envelope: %v", err)
	}

	if errEnvelope.Error.Code != models.ErrCodeNotFound {
		t.Errorf("expected code NOT_FOUND, got %s", errEnvelope.Error.Code)
	}
}

func TestServiceUnavailableErrorEnvelope(t *testing.T) {
	r := setupTestRouter()

	req := httptest.NewRequest(http.MethodGet, "/v1/resolve?service=unregistered-svc", nil)
	rec := httptest.NewRecorder()
	r.ServeHTTP(rec, req)

	if rec.Code != http.StatusServiceUnavailable {
		t.Fatalf("expected status 503, got %d", rec.Code)
	}

	var errEnvelope models.ApiErrorResponse
	if err := json.Unmarshal(rec.Body.Bytes(), &errEnvelope); err != nil {
		t.Fatalf("failed to parse ApiErrorResponse envelope: %v", err)
	}

	if errEnvelope.Error.Code != models.ErrCodeServiceUnavailable {
		t.Errorf("expected code SERVICE_UNAVAILABLE, got %s", errEnvelope.Error.Code)
	}
}

func TestMutationIdempotencyCache(t *testing.T) {
	r := setupTestRouter()

	payload := map[string]interface{}{
		"name":     "idempotent-service",
		"host":     "idempotent-service-host",
		"port":     9090,
		"protocol": "http",
	}
	body, _ := json.Marshal(payload)

	// First call
	req1 := httptest.NewRequest(http.MethodPost, "/v1/register", bytes.NewBuffer(body))
	req1.Header.Set("Content-Type", "application/json")
	req1.Header.Set("x-idempotency-key", "idem-unique-key-999")

	rec1 := httptest.NewRecorder()
	r.ServeHTTP(rec1, req1)

	if rec1.Code != http.StatusCreated {
		t.Fatalf("first request failed with status %d", rec1.Code)
	}
	if rec1.Header().Get("x-cache-hit") == "true" {
		t.Errorf("first request should not be a cache hit")
	}

	// Second call with same idempotency key
	req2 := httptest.NewRequest(http.MethodPost, "/v1/register", bytes.NewBuffer(body))
	req2.Header.Set("Content-Type", "application/json")
	req2.Header.Set("x-idempotency-key", "idem-unique-key-999")

	rec2 := httptest.NewRecorder()
	r.ServeHTTP(rec2, req2)

	if rec2.Code != http.StatusOK {
		t.Fatalf("second request failed with status %d", rec2.Code)
	}
	if rec2.Header().Get("x-cache-hit") != "true" {
		t.Errorf("second request should have header x-cache-hit: true")
	}
}
