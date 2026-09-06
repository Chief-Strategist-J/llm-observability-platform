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
	"github.com/llm-observability/platform/packages/configs/llm-obs-infra/service-discovery/security"
	"github.com/llm-observability/platform/packages/configs/llm-obs-infra/service-discovery/server"
)

func TestSecuritySSRFMetadataRejection(t *testing.T) {
	err := security.ValidateEndpoint("169.254.169.254", 80, true)
	if err == nil {
		t.Fatal("expected SSRF error when validating 169.254.169.254 cloud metadata IP")
	}

	errLoopback := security.ValidateEndpoint("127.0.0.1", 8080, true)
	if errLoopback == nil {
		t.Fatal("expected error when validating 127.0.0.1 loopback IP with RFC1918 enforcement")
	}

	errValidRFC := security.ValidateEndpoint("10.0.0.15", 8080, true)
	if errValidRFC != nil {
		t.Fatalf("expected valid RFC 1918 IP 10.0.0.15 to pass, got error: %v", errValidRFC)
	}
}

func TestSecurityProtocolValidation(t *testing.T) {
	if err := security.ValidateProtocol("http"); err != nil {
		t.Errorf("expected http to be valid, got %v", err)
	}
	if err := security.ValidateProtocol("tcp"); err != nil {
		t.Errorf("expected tcp to be valid, got %v", err)
	}
	if err := security.ValidateProtocol("exec"); err == nil {
		t.Error("expected exec protocol to be rejected")
	}
}

func TestBearerAuthenticationMiddleware(t *testing.T) {
	reg := registry.NewRegistry(registry.DefaultInstanceDefaults)
	disc := discovery.NewDiscovery(reg)
	secCfg := models.SecurityConfig{
		AuthToken:      "super-secret-token-123",
		EnforceRFC1918: false,
	}
	r := server.NewRouter(reg, disc, secCfg)

	payload := map[string]interface{}{
		"name":     "auth-svc",
		"host":     "10.0.0.5",
		"port":     8080,
		"protocol": "http",
	}
	body, _ := json.Marshal(payload)

	// 1. Call without Authorization header -> should return 401 Unauthorized
	reqNoAuth := httptest.NewRequest(http.MethodPost, "/v1/register", bytes.NewBuffer(body))
	reqNoAuth.Header.Set("Content-Type", "application/json")
	recNoAuth := httptest.NewRecorder()
	r.ServeHTTP(recNoAuth, reqNoAuth)

	if recNoAuth.Code != http.StatusUnauthorized {
		t.Fatalf("expected 401 Unauthorized without auth header, got %d", recNoAuth.Code)
	}

	// 2. Call with invalid token -> should return 401 Unauthorized
	reqBadAuth := httptest.NewRequest(http.MethodPost, "/v1/register", bytes.NewBuffer(body))
	reqBadAuth.Header.Set("Content-Type", "application/json")
	reqBadAuth.Header.Set("Authorization", "Bearer wrong-token")
	recBadAuth := httptest.NewRecorder()
	r.ServeHTTP(recBadAuth, reqBadAuth)

	if recBadAuth.Code != http.StatusUnauthorized {
		t.Fatalf("expected 401 Unauthorized with bad token, got %d", recBadAuth.Code)
	}

	// 3. Call with valid token -> should return 201 Created
	reqValidAuth := httptest.NewRequest(http.MethodPost, "/v1/register", bytes.NewBuffer(body))
	reqValidAuth.Header.Set("Content-Type", "application/json")
	reqValidAuth.Header.Set("Authorization", "Bearer super-secret-token-123")
	recValidAuth := httptest.NewRecorder()
	r.ServeHTTP(recValidAuth, reqValidAuth)

	if recValidAuth.Code != http.StatusCreated {
		t.Fatalf("expected 201 Created with valid token, got %d: %s", recValidAuth.Code, recValidAuth.Body.String())
	}
}
