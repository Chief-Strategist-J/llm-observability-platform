package tests

import (
	"bytes"
	"context"
	"encoding/json"
	"net"
	"net/http"
	"net/http/httptest"
	"os"
	"path/filepath"
	"sync"
	"testing"
	"time"

	"github.com/llm-observability/platform/packages/configs/llm-obs-infra/service-discovery/discovery"
	"github.com/llm-observability/platform/packages/configs/llm-obs-infra/service-discovery/loadbalancer"
	"github.com/llm-observability/platform/packages/configs/llm-obs-infra/service-discovery/models"
	"github.com/llm-observability/platform/packages/configs/llm-obs-infra/service-discovery/registry"
	"github.com/llm-observability/platform/packages/configs/llm-obs-infra/service-discovery/server"
	"github.com/llm-observability/platform/packages/configs/llm-obs-infra/service-discovery/tracing"
	"github.com/llm-observability/platform/packages/configs/llm-obs-infra/service-discovery/traefik"
)

func TestCriticalEndToEndSystemIntegration(t *testing.T) {
	// 1. Setup Isolated Temporary Directory for Traefik File Provider Exporter
	tmpDir, err := os.MkdirTemp("", "sd-critical-test-*")
	if err != nil {
		t.Fatalf("failed to create temp dir: %v", err)
	}
	defer os.RemoveAll(tmpDir)

	traefikOutPath := filepath.Join(tmpDir, "discovery.yml")

	// 2. Initialize Core Subsystems
	regDefaults := models.InstanceDefaults{
		Weight:              100,
		HealthCheckInterval: 50 * time.Millisecond,
		HealthCheckTimeout:  200 * time.Millisecond,
	}
	reg := registry.NewRegistry(regDefaults)
	disc := discovery.NewDiscovery(reg)

	// Lease Manager (Sufficient TTL for multi-step integration assertions)
	leaseCfg := models.LeaseManagerConfig{
		SweepInterval: 100 * time.Millisecond,
		HeartbeatTTL:  10 * time.Second,
		EvictionTTL:   30 * time.Second,
	}
	leaseMgr := registry.NewLeaseManager(reg, leaseCfg)
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()
	go leaseMgr.Start(ctx)

	// Health Prober
	proberCfg := models.HealthProberConfig{
		ProbeInterval:    50 * time.Millisecond,
		MaxConcurrent:    10,
		DefaultSuccessTh: 1,
		DefaultFailureTh: 2,
	}
	prober := registry.NewHealthProber(reg, proberCfg)
	go prober.Start(ctx)

	// Traefik Exporter
	expCfg := traefik.ExporterConfig{
		OutputPath:         traefikOutPath,
		DefaultDomain:      "llmobs.local",
		DefaultEntryPoints: []string{"web"},
		DefaultMiddlewares: []string{},
	}
	exporter := traefik.NewExporter(reg, expCfg)
	eventsCh := reg.Subscribe()
	go exporter.Start(eventsCh)

	// REST Gateway Router
	router := server.NewRouter(reg, disc)
	httpHandler := tracing.Middleware(router)

	// 3. Test Mock Target Server Lifecycle (Node 1 & Node 2)
	var node1Status int = http.StatusOK
	var node1Mu sync.Mutex

	node1Server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		node1Mu.Lock()
		defer node1Mu.Unlock()
		w.WriteHeader(node1Status)
	}))
	defer node1Server.Close()
	node1Port := node1Server.Listener.Addr().(*net.TCPAddr).Port

	node2Server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
	}))
	defer node2Server.Close()
	node2Port := node2Server.Listener.Addr().(*net.TCPAddr).Port

	// 4. Register Target Instances via REST Gateway API with Idempotency Key
	idemKey1 := "idem-critical-node1"
	regPayload1 := map[string]any{
		"name":     "ai-service",
		"host":     "127.0.0.1",
		"port":     node1Port,
		"protocol": "http",
		"healthCheck": map[string]any{
			"protocol": "http",
			"path":     "/health",
		},
	}
	bodyBytes1, _ := json.Marshal(regPayload1)
	req1 := httptest.NewRequest(http.MethodPost, "/v1/register", bytes.NewReader(bodyBytes1))
	req1.Header.Set("Content-Type", "application/json")
	req1.Header.Set("x-idempotency-key", idemKey1)
	req1.Header.Set("x-request-id", "req-crit-101")
	req1.Header.Set("x-correlation-id", "corr-crit-101")
	req1.Header.Set("x-causation-id", "caus-crit-101")
	req1.Header.Set("x-tenant-id", "tenant-quality")

	rec1 := httptest.NewRecorder()
	httpHandler.ServeHTTP(rec1, req1)

	if rec1.Code != http.StatusCreated {
		t.Fatalf("expected 201 Created for node1 registration, got %d: %s", rec1.Code, rec1.Body.String())
	}

	// Verify Header Propagation
	if rec1.Header().Get("x-request-id") != "req-crit-101" {
		t.Errorf("expected header x-request-id: req-crit-101, got %s", rec1.Header().Get("x-request-id"))
	}
	if rec1.Header().Get("x-tenant-id") != "tenant-quality" {
		t.Errorf("expected header x-tenant-id: tenant-quality, got %s", rec1.Header().Get("x-tenant-id"))
	}

	// Unmarshal & Validate Standard Success Envelope
	var resp1 models.ApiResponse[models.ServiceInstance]
	if err := json.Unmarshal(rec1.Body.Bytes(), &resp1); err != nil {
		t.Fatalf("failed to unmarshal register response: %v", err)
	}
	if !resp1.Success || resp1.StatusCode != http.StatusCreated || resp1.Data.Name != "ai-service" {
		t.Errorf("invalid response envelope data: %+v", resp1)
	}

	// Register Node 2
	idemKey2 := "idem-critical-node2"
	regPayload2 := map[string]any{
		"name":     "ai-service",
		"host":     "127.0.0.1",
		"port":     node2Port,
		"protocol": "http",
		"healthCheck": map[string]any{
			"protocol": "http",
			"path":     "/health",
		},
	}
	bodyBytes2, _ := json.Marshal(regPayload2)
	req2 := httptest.NewRequest(http.MethodPost, "/v1/register", bytes.NewReader(bodyBytes2))
	req2.Header.Set("Content-Type", "application/json")
	req2.Header.Set("x-idempotency-key", idemKey2)
	rec2 := httptest.NewRecorder()
	httpHandler.ServeHTTP(rec2, req2)
	if rec2.Code != http.StatusCreated {
		t.Fatalf("expected 201 Created for node2 registration, got %d", rec2.Code)
	}

	// 5. Test Idempotency Engine under 50 Concurrent Retries for Node 1
	var wg sync.WaitGroup
	var cacheHits int64
	var hitMu sync.Mutex

	for i := 0; i < 50; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			reqIdem := httptest.NewRequest(http.MethodPost, "/v1/register", bytes.NewReader(bodyBytes1))
			reqIdem.Header.Set("Content-Type", "application/json")
			reqIdem.Header.Set("x-idempotency-key", idemKey1)
			recIdem := httptest.NewRecorder()
			httpHandler.ServeHTTP(recIdem, reqIdem)

			if recIdem.Header().Get("x-cache-hit") == "true" {
				hitMu.Lock()
				cacheHits++
				hitMu.Unlock()
			}
		}()
	}
	wg.Wait()

	if cacheHits < 45 {
		t.Errorf("expected at least 45 idempotency cache hits out of 50 concurrent retries, got %d", cacheHits)
	}

	// 6. Test Active Health Prober & Dynamic Failure Failover
	// Wait for initial prober sweep
	time.Sleep(150 * time.Millisecond)

	// Verify exactly 2 healthy nodes initially
	instances, err := disc.ResolveAll("ai-service")
	if err != nil || len(instances) != 2 {
		t.Fatalf("expected 2 healthy nodes initially, got %d, err: %v", len(instances), err)
	}

	// Simulate Node 1 Failure (Returns 500 Internal Server Error)
	node1Mu.Lock()
	node1Status = http.StatusInternalServerError
	node1Mu.Unlock()

	// Wait for active prober 2-strike failure threshold to flip node 1 to UNHEALTHY
	time.Sleep(200 * time.Millisecond)

	// Verify Discovery dynamically routes ONLY to surviving healthy Node 2
	instancesAfterFailure, err := disc.ResolveAll("ai-service")
	if err != nil || len(instancesAfterFailure) != 1 {
		t.Fatalf("expected 1 healthy node after node1 failure, got %d, err: %v", len(instancesAfterFailure), err)
	}
	if instancesAfterFailure[0].Port != node2Port {
		t.Errorf("expected traffic to route to Node 2 (port %d), got port %d", node2Port, instancesAfterFailure[0].Port)
	}

	// 7. Test Dual-Resolution Fallback for Unregistered Target
	fallbackInst, fallbackUsed := disc.ResolveWithFallback("legacy-analytics", "10.0.0.50", 9090, "http")
	if !fallbackUsed {
		t.Errorf("expected fallbackUsed: true for unregistered target")
	}
	if fallbackInst.Endpoint() != "http://10.0.0.50:9090" {
		t.Errorf("expected fallback endpoint http://10.0.0.50:9090, got %s", fallbackInst.Endpoint())
	}

	// 8. Test Traefik File Provider Exporter Auto-Generation
	time.Sleep(100 * time.Millisecond)
	if _, err := os.Stat(traefikOutPath); os.IsNotExist(err) {
		t.Fatalf("expected Traefik discovery.yml file to exist at %s", traefikOutPath)
	}
	yamlBytes, err := os.ReadFile(traefikOutPath)
	if err != nil || len(yamlBytes) == 0 {
		t.Fatalf("failed to read generated discovery.yml file: %v", err)
	}

	// Verify YAML content structure
	yamlStr := string(yamlBytes)
	if !bytes.Contains(yamlBytes, []byte("ai-service")) || !bytes.Contains(yamlBytes, []byte("Host(`ai-service.llmobs.local`)")) {
		t.Errorf("generated discovery.yml missing expected Traefik router rules:\n%s", yamlStr)
	}

	// 9. Test Circuit Breaker & Load Balancer Integration
	cb := loadbalancer.NewCircuitBreaker(models.DefaultCircuitBreakerConfig)
	if cb.State() != models.CircuitClosed {
		t.Errorf("expected circuit breaker state CLOSED, got %s", cb.State())
	}

	t.Logf("CRITICAL SYSTEM INTEGRATION TEST PASSED SUCCESSFULLY!")
}
