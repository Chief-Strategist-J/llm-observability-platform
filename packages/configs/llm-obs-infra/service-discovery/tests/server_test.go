package tests

import (
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"

	"github.com/llm-observability/platform/packages/configs/llm-obs-infra/service-discovery/discovery"
	"github.com/llm-observability/platform/packages/configs/llm-obs-infra/service-discovery/registry"
	"github.com/llm-observability/platform/packages/configs/llm-obs-infra/service-discovery/server"
)

func newTestRouter() (*server.Router, *registry.Registry) {
	reg := newTestRegistry()
	disc := discovery.NewDiscovery(reg)
	router := server.NewRouter(reg, disc)
	return router, reg
}

func TestRegisterEndpoint(t *testing.T) {
	router, _ := newTestRouter()

	body := `{"name":"test-svc","host":"localhost","port":9090,"protocol":"http","healthCheck":{"protocol":"http","path":"/health"}}`
	req := httptest.NewRequest("POST", "/v1/register", strings.NewReader(body))
	req.Header.Set("Content-Type", "application/json")
	rr := httptest.NewRecorder()

	router.ServeHTTP(rr, req)

	if rr.Code != http.StatusCreated {
		t.Fatalf("expected 201, got %d: %s", rr.Code, rr.Body.String())
	}

	var result map[string]interface{}
	json.Unmarshal(rr.Body.Bytes(), &result)

	if result["name"] != "test-svc" {
		t.Fatalf("expected test-svc, got %v", result["name"])
	}
	if result["id"] == nil || result["id"] == "" {
		t.Fatal("expected auto-generated id")
	}
}

func TestResolveEndpointAPI(t *testing.T) {
	router, reg := newTestRouter()
	reg.Register(newTestInstance("api-svc", "localhost", 7070))

	req := httptest.NewRequest("GET", "/v1/resolve?service=api-svc", nil)
	rr := httptest.NewRecorder()

	router.ServeHTTP(rr, req)

	if rr.Code != http.StatusOK {
		t.Fatalf("expected 200, got %d: %s", rr.Code, rr.Body.String())
	}

	var result map[string]interface{}
	json.Unmarshal(rr.Body.Bytes(), &result)

	if result["endpoint"] != "http://localhost:7070" {
		t.Fatalf("expected http://localhost:7070, got %v", result["endpoint"])
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
	reg.Register(newTestInstance("svc-a", "localhost", 8080))
	reg.Register(newTestInstance("svc-b", "localhost", 8081))

	req := httptest.NewRequest("GET", "/v1/services", nil)
	rr := httptest.NewRecorder()

	router.ServeHTTP(rr, req)

	if rr.Code != http.StatusOK {
		t.Fatalf("expected 200, got %d", rr.Code)
	}

	var result map[string]interface{}
	json.Unmarshal(rr.Body.Bytes(), &result)

	if len(result) != 2 {
		t.Fatalf("expected 2 services, got %d", len(result))
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
	inst := reg.Register(newTestInstance("hb-svc", "localhost", 8080))

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
	inst := reg.Register(newTestInstance("dereg-svc", "localhost", 8080))

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
