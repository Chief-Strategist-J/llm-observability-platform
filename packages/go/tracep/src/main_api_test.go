package main

import (
	"bytes"
	"database/sql"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"os"
	"testing"
	"time"

	_ "modernc.org/sqlite"
)

func TestQueryAPIs(t *testing.T) {
	tempDB := "./temp_api_test.db"
	defer os.Remove(tempDB)
	defer os.Remove(tempDB + "-wal")
	defer os.Remove(tempDB + "-shm")

	db, err := sql.Open("sqlite", tempDB)
	if err != nil {
		t.Fatalf("failed to open sqlite: %v", err)
	}
	db.SetMaxOpenConns(1)
	_, _ = db.Exec("PRAGMA journal_mode=WAL; PRAGMA synchronous=NORMAL; PRAGMA busy_timeout=5000;")
	defer db.Close()

	runMigrations(db)

	srv := &Server{
		db:    db,
		token: "secret-key",
	}

	// 1. Test Ingest
	payload := generateMockOTLPPayload("trace-123", "span-456")
	reqIngest, _ := http.NewRequest(http.MethodPost, "/v1/traces", bytes.NewReader(payload))
	reqIngest.Header.Set("Authorization", "Bearer secret-key")
	reqIngest.Header.Set("Content-Type", "application/json")
	wIngest := httptest.NewRecorder()
	srv.handleIngest(wIngest, reqIngest)

	if wIngest.Code != http.StatusOK {
		t.Errorf("Ingest failed: status code %d", wIngest.Code)
	}

	// 2. Test /health
	reqHealth, _ := http.NewRequest(http.MethodGet, "/health", nil)
	wHealth := httptest.NewRecorder()
	srv.handleHealth(wHealth, reqHealth)
	if wHealth.Code != http.StatusOK {
		t.Errorf("/health status code %d", wHealth.Code)
	}

	// 3. Test /traces
	reqTraces, _ := http.NewRequest(http.MethodGet, "/traces?class=TestService", nil)
	reqTraces.Header.Set("Authorization", "Bearer secret-key")
	wTraces := httptest.NewRecorder()
	srv.handleTraces(wTraces, reqTraces)
	if wTraces.Code != http.StatusOK {
		t.Errorf("/traces status code %d", wTraces.Code)
	}
	var tracesResponse map[string]interface{}
	_ = json.Unmarshal(wTraces.Body.Bytes(), &tracesResponse)
	if total, ok := tracesResponse["total"].(float64); !ok || total != 1 {
		t.Errorf("expected 1 trace, got %v", tracesResponse["total"])
	}

	// 4. Test /traces/:tid
	reqTree, _ := http.NewRequest(http.MethodGet, "/traces/trace-123", nil)
	reqTree.Header.Set("Authorization", "Bearer secret-key")
	wTree := httptest.NewRecorder()
	srv.handleSingleTraceRoute(wTree, reqTree)
	if wTree.Code != http.StatusOK {
		t.Errorf("/traces/:tid status code %d", wTree.Code)
	}
	var traceTree TraceDetail
	_ = json.Unmarshal(wTree.Body.Bytes(), &traceTree)
	if traceTree.TID != "trace-123" || len(traceTree.Tree) != 1 {
		t.Errorf("invalid trace tree response: %+v", traceTree)
	}

	// 5. Test /traces/:tid/spans
	reqFlatSpans, _ := http.NewRequest(http.MethodGet, "/traces/trace-123/spans", nil)
	reqFlatSpans.Header.Set("Authorization", "Bearer secret-key")
	wFlatSpans := httptest.NewRecorder()
	srv.handleSingleTraceRoute(wFlatSpans, reqFlatSpans)
	if wFlatSpans.Code != http.StatusOK {
		t.Errorf("/traces/:tid/spans status code %d", wFlatSpans.Code)
	}
	var flatSpans []interface{}
	_ = json.Unmarshal(wFlatSpans.Body.Bytes(), &flatSpans)
	if len(flatSpans) != 1 {
		t.Errorf("expected 1 flat span, got %d", len(flatSpans))
	}

	// 6. Test /spans/:sid
	reqSpan, _ := http.NewRequest(http.MethodGet, "/spans/span-456", nil)
	reqSpan.Header.Set("Authorization", "Bearer secret-key")
	wSpan := httptest.NewRecorder()
	srv.handleSingleSpanRoute(wSpan, reqSpan)
	if wSpan.Code != http.StatusOK {
		t.Errorf("/spans/:sid status code %d", wSpan.Code)
	}
	var spanNode SpanNode
	_ = json.Unmarshal(wSpan.Body.Bytes(), &spanNode)
	if spanNode.SID != "span-456" || len(spanNode.Steps) != 1 {
		t.Errorf("invalid span node response: %+v", spanNode)
	}

	// 7. Test /classes
	reqClasses, _ := http.NewRequest(http.MethodGet, "/classes", nil)
	reqClasses.Header.Set("Authorization", "Bearer secret-key")
	wClasses := httptest.NewRecorder()
	srv.handleClasses(wClasses, reqClasses)
	if wClasses.Code != http.StatusOK {
		t.Errorf("/classes status code %d", wClasses.Code)
	}
	var classes []string
	_ = json.Unmarshal(wClasses.Body.Bytes(), &classes)
	if len(classes) != 1 || classes[0] != "TestService" {
		t.Errorf("expected classes [TestService], got %v", classes)
	}

	// 8. Test /functions
	reqFuncs, _ := http.NewRequest(http.MethodGet, "/functions?class=TestService", nil)
	reqFuncs.Header.Set("Authorization", "Bearer secret-key")
	wFuncs := httptest.NewRecorder()
	srv.handleFunctions(wFuncs, reqFuncs)
	if wFuncs.Code != http.StatusOK {
		t.Errorf("/functions status code %d", wFuncs.Code)
	}
	var funcs []string
	_ = json.Unmarshal(wFuncs.Body.Bytes(), &funcs)
	if len(funcs) != 1 || funcs[0] != "testFunc" {
		t.Errorf("expected functions [testFunc], got %v", funcs)
	}

	time.Sleep(10 * time.Millisecond)
}

func TestAuthRejected(t *testing.T) {
	tempDB := "./temp_auth_test.db"
	defer os.Remove(tempDB)
	defer os.Remove(tempDB + "-wal")
	defer os.Remove(tempDB + "-shm")

	db, err := sql.Open("sqlite", tempDB)
	if err != nil {
		t.Fatalf("failed to open sqlite: %v", err)
	}
	db.SetMaxOpenConns(1)
	_, _ = db.Exec("PRAGMA journal_mode=WAL; PRAGMA synchronous=NORMAL; PRAGMA busy_timeout=5000;")
	defer db.Close()
	runMigrations(db)

	srv := &Server{db: db, token: "secret-key"}

	endpoints := []struct {
		method string
		path   string
		handler http.HandlerFunc
	}{
		{"GET", "/traces", srv.handleTraces},
		{"GET", "/traces/any-tid", srv.handleSingleTraceRoute},
		{"GET", "/spans/any-sid", srv.handleSingleSpanRoute},
		{"GET", "/classes", srv.handleClasses},
		{"GET", "/functions", srv.handleFunctions},
	}

	for _, ep := range endpoints {
		// No token — must reject
		req, _ := http.NewRequest(ep.method, ep.path, nil)
		w := httptest.NewRecorder()
		ep.handler(w, req)
		if w.Code != http.StatusUnauthorized {
			t.Errorf("%s %s: expected 401 with no token, got %d", ep.method, ep.path, w.Code)
		}

		// Wrong token — must reject
		reqWrong, _ := http.NewRequest(ep.method, ep.path, nil)
		reqWrong.Header.Set("Authorization", "Bearer wrong-token")
		wWrong := httptest.NewRecorder()
		ep.handler(wWrong, reqWrong)
		if wWrong.Code != http.StatusUnauthorized {
			t.Errorf("%s %s: expected 401 with wrong token, got %d", ep.method, ep.path, wWrong.Code)
		}
	}

	// /health must always be accessible without auth
	reqHealth, _ := http.NewRequest("GET", "/health", nil)
	wHealth := httptest.NewRecorder()
	srv.handleHealth(wHealth, reqHealth)
	if wHealth.Code != http.StatusOK {
		t.Errorf("/health should be public, got %d", wHealth.Code)
	}
}
