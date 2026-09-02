package tests

import (
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"

	"github.com/llm-observability/platform/packages/configs/llm-obs-infra/service-discovery/discovery"
	"github.com/llm-observability/platform/packages/configs/llm-obs-infra/service-discovery/models"
	"github.com/llm-observability/platform/packages/configs/llm-obs-infra/service-discovery/registry"
	"github.com/llm-observability/platform/packages/configs/llm-obs-infra/service-discovery/server"
)

func newTestRouter() (*server.Router, *registry.Registry) {
	reg := newTestRegistry()
	disc := discovery.NewDiscovery(reg)
	router := server.NewRouter(reg, disc, models.SecurityConfig{EnforceRFC1918: false})
	return router, reg
}

func TestRegisterEndpoint(t *testing.T) {
	router, _ := newTestRouter()

	body := `{"name":"test-svc","host":"test-svc-host","port":9090,"protocol":"http","healthCheck":{"protocol":"http","path":"/health"}}`
	req := httptest.NewRequest("POST", "/v1/register", strings.NewReader(body))
	req.Header.Set("Content-Type", "application/json")
	rr := httptest.NewRecorder()

	router.ServeHTTP(rr, req)

	if rr.Code != http.StatusCreated {
		t.Fatalf("expected 201, got %d: %s", rr.Code, rr.Body.String())
	}

	var envelope models.ApiResponse[models.ServiceInstance]
	if err := json.Unmarshal(rr.Body.Bytes(), &envelope); err != nil {
		t.Fatalf("failed to unmarshal register response: %v", err)
	}

	if envelope.Data.Name != "test-svc" {
		t.Fatalf("expected test-svc, got %v", envelope.Data.Name)
	}
	if envelope.Data.ID == "" {
		t.Fatal("expected auto-generated id")
	}
}

func TestResolveEndpointAPI(t *testing.T) {
	router, reg := newTestRouter()
	reg.Register(newTestInstance("api-svc", "api-svc-host", 7070))

	req := httptest.NewRequest("GET", "/v1/resolve?service=api-svc", nil)
	rr := httptest.NewRecorder()

	router.ServeHTTP(rr, req)

	if rr.Code != http.StatusOK {
		t.Fatalf("expected 200, got %d: %s", rr.Code, rr.Body.String())
	}

	var envelope models.ApiResponse[map[string]interface{}]
	if err := json.Unmarshal(rr.Body.Bytes(), &envelope); err != nil {
		t.Fatalf("failed to unmarshal resolve response: %v", err)
	}

	if envelope.Data["endpoint"] != "http://api-svc-host:7070" {
		t.Fatalf("expected http://api-svc-host:7070, got %v", envelope.Data["endpoint"])
	}
}

func TestResolveEndpointNotFound(t *testing.T) {
	router, _ := newTestRouter()

	req := httptest.NewRequest("GET", "/v1/resolve?service=nonexistent", nil)
	rr := httptest.NewRecorder()

	router.ServeHTTP(rr, req)

	if rr.Code != http.StatusServiceUnavailable {
		t.Fatalf("expected 503, got %d", rr.Code)
	}
}

func TestResolveMissingParam(t *testing.T) {
	router, _ := newTestRouter()

	req := httptest.NewRequest("GET", "/v1/resolve", nil)
	rr := httptest.NewRecorder()

	router.ServeHTTP(rr, req)

	if rr.Code != http.StatusBadRequest {
		t.Fatalf("expected 400, got %d", rr.Code)
	}
}

func TestListServicesEndpoint(t *testing.T) {
	router, reg := newTestRouter()
	reg.Register(newTestInstance("svc-a", "svc-a-host", 8080))
	reg.Register(newTestInstance("svc-b", "svc-b-host", 8081))

	req := httptest.NewRequest("GET", "/v1/services", nil)
	rr := httptest.NewRecorder()

	router.ServeHTTP(rr, req)

	if rr.Code != http.StatusOK {
		t.Fatalf("expected 200, got %d", rr.Code)
	}

	var envelope models.ApiResponse[map[string][]models.ServiceInstance]
	if err := json.Unmarshal(rr.Body.Bytes(), &envelope); err != nil {
		t.Fatalf("failed to unmarshal services response: %v", err)
	}

	if len(envelope.Data) != 2 {
		t.Fatalf("expected 2 services, got %d", len(envelope.Data))
	}
}

func TestHealthEndpoint(t *testing.T) {
	router, _ := newTestRouter()

	req := httptest.NewRequest("GET", "/health", nil)
	rr := httptest.NewRecorder()

	router.ServeHTTP(rr, req)

	if rr.Code != http.StatusOK {
		t.Fatalf("expected 200, got %d", rr.Code)
	}
}

func TestHeartbeatEndpoint(t *testing.T) {
	router, reg := newTestRouter()
	inst := reg.Register(newTestInstance("hb-svc", "hb-svc-host", 8080))

	body := `{"name":"hb-svc","instanceId":"` + inst.ID + `"}`
	req := httptest.NewRequest("POST", "/v1/heartbeat", strings.NewReader(body))
	req.Header.Set("Content-Type", "application/json")
	rr := httptest.NewRecorder()

	router.ServeHTTP(rr, req)

	if rr.Code != http.StatusOK {
		t.Fatalf("expected 200, got %d: %s", rr.Code, rr.Body.String())
	}
}

func TestDeregisterEndpoint(t *testing.T) {
	router, reg := newTestRouter()
	inst := reg.Register(newTestInstance("dereg-svc", "dereg-svc-host", 8080))

	body := `{"name":"dereg-svc","instanceId":"` + inst.ID + `"}`
	req := httptest.NewRequest("POST", "/v1/deregister", strings.NewReader(body))
	req.Header.Set("Content-Type", "application/json")
	rr := httptest.NewRecorder()

	router.ServeHTTP(rr, req)

	if rr.Code != http.StatusOK {
		t.Fatalf("expected 200, got %d: %s", rr.Code, rr.Body.String())
	}

	all := reg.GetAll("dereg-svc")
	if len(all) != 0 {
		t.Fatalf("expected 0 instances after deregister, got %d", len(all))
	}
}
