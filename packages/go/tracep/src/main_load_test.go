package main

import (
	"bytes"
	"database/sql"
	"encoding/json"
	"fmt"
	"net/http"
	"net/http/httptest"
	"os"
	"sync"
	"sync/atomic"
	"testing"
	"time"

	_ "modernc.org/sqlite"
)

func generateMockOTLPPayload(traceID, spanID string) []byte {
	payload := OtlpPayload{
		ResourceSpans: []ResourceSpans{
			{
				ScopeSpans: []ScopeSpans{
					{
						Spans: []OtlpSpan{
							{
								TraceID:           traceID,
								SpanID:            spanID,
								Name:              "test-operation",
								StartTimeUnixNano: fmt.Sprintf("%d", time.Now().UnixNano()),
								EndTimeUnixNano:   fmt.Sprintf("%d", time.Now().Add(50*time.Millisecond).UnixNano()),
								Attributes: []KeyValue{
									{Key: "code.namespace", Value: ValueHolder{StringValue: "TestService"}},
									{Key: "code.function", Value: ValueHolder{StringValue: "testFunc"}},
								},
								Events: []OtlpEvent{
									{
										TimeUnixNano: fmt.Sprintf("%d", time.Now().UnixNano()),
										Name:         "db.query",
										Attributes: []KeyValue{
											{Key: "message", Value: ValueHolder{StringValue: "selecting rows"}},
											{Key: "level", Value: ValueHolder{StringValue: "info"}},
										},
									},
								},
								Status: &OtlpStatus{
									Code: 1, // StatusCode Ok
								},
							},
						},
					},
				},
			},
		},
	}
	data, _ := json.Marshal(payload)
	return data
}

func TestLoad10kRequests(t *testing.T) {
	tempDB := "./temp_load_test.db"
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
		token: "secret",
	}

	ts := httptest.NewServer(http.HandlerFunc(srv.handleIngest))
	defer ts.Close()

	client := &http.Client{
		Transport: &http.Transport{
			MaxIdleConns:        100,
			MaxIdleConnsPerHost: 100,
		},
	}

	totalRequests := 10000
	concurrency := 100
	var successCount int64
	var failureCount int64

	var wg sync.WaitGroup
	reqChan := make(chan int, totalRequests)
	for i := 0; i < totalRequests; i++ {
		reqChan <- i
	}
	close(reqChan)

	startTime := time.Now()

	for w := 0; w < concurrency; w++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			for i := range reqChan {
				// Format valid trace ID (32 hex characters) and span ID (16 hex characters)
				traceID := fmt.Sprintf("%032x", i)
				spanID := fmt.Sprintf("%016x", i)

				payload := generateMockOTLPPayload(traceID, spanID)
				req, err := http.NewRequest(http.MethodPost, ts.URL+"/v1/traces", bytes.NewReader(payload))
				if err != nil {
					atomic.AddInt64(&failureCount, 1)
					continue
				}
				req.Header.Set("Authorization", "Bearer secret")
				req.Header.Set("Content-Type", "application/json")

				resp, err := client.Do(req)
				if err != nil {
					atomic.AddInt64(&failureCount, 1)
					continue
				}

				if resp.StatusCode == http.StatusOK {
					atomic.AddInt64(&successCount, 1)
				} else {
					atomic.AddInt64(&failureCount, 1)
				}
				resp.Body.Close()
			}
		}()
	}

	wg.Wait()
	duration := time.Since(startTime)

	t.Logf("Completed %d requests in %v", totalRequests, duration)
	t.Logf("Throughput: %.2f req/sec", float64(totalRequests)/duration.Seconds())
	t.Logf("Successes: %d, Failures: %d", successCount, failureCount)

	if successCount != int64(totalRequests) {
		t.Errorf("expected %d successes, got %d", totalRequests, successCount)
	}

	var count int
	err = db.QueryRow("SELECT COUNT(*) FROM traces").Scan(&count)
	if err != nil {
		t.Fatalf("failed to query traces count: %v", err)
	}
	if count != totalRequests {
		t.Errorf("expected %d traces stored in DB, got %d", totalRequests, count)
	}
}
