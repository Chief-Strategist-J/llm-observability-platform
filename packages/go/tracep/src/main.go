package main

import (
	"database/sql"
	"encoding/hex"
	"encoding/json"
	"io"
	"log"
	"net/http"
	"os"
	"path/filepath"
	"strconv"
	"strings"
	"sync"
	"time"

	coltracepb "go.opentelemetry.io/proto/otlp/collector/trace/v1"
	"google.golang.org/protobuf/proto"
	_ "modernc.org/sqlite"
)

// OTLP JSON structures
type OtlpPayload struct {
	ResourceSpans []ResourceSpans `json:"resourceSpans"`
}

type ResourceSpans struct {
	Resource   *Resource    `json:"resource,omitempty"`
	ScopeSpans []ScopeSpans `json:"scopeSpans"`
}

type Resource struct {
	Attributes []KeyValue `json:"attributes,omitempty"`
}

type ScopeSpans struct {
	Spans []OtlpSpan `json:"spans"`
}

type OtlpSpan struct {
	TraceID           string      `json:"traceId"`
	SpanID            string      `json:"spanId"`
	ParentSpanID      string      `json:"parentSpanId,omitempty"`
	Name              string      `json:"name"`
	StartTimeUnixNano string      `json:"startTimeUnixNano"`
	EndTimeUnixNano   string      `json:"endTimeUnixNano"`
	Attributes        []KeyValue  `json:"attributes,omitempty"`
	Events            []OtlpEvent `json:"events,omitempty"`
	Status            *OtlpStatus `json:"status,omitempty"`
}

type KeyValue struct {
	Key   string      `json:"key"`
	Value ValueHolder `json:"value"`
}

type ValueHolder struct {
	StringValue string `json:"stringValue,omitempty"`
	IntValue    string `json:"intValue,omitempty"`
}

type OtlpEvent struct {
	TimeUnixNano string     `json:"timeUnixNano"`
	Name         string     `json:"name"`
	Attributes   []KeyValue `json:"attributes,omitempty"`
}

type OtlpStatus struct {
	Code    int    `json:"code,omitempty"`
	Message string `json:"message,omitempty"`
}

// Tree Nodes for full tree response
type Step struct {
	Step    string `json:"step"`
	Message string `json:"message"`
	Level   string `json:"level"`
	TS      int64  `json:"ts"`
}

type SpanNode struct {
	SID        string                 `json:"sid"`
	Class      string                 `json:"class"`
	Function   string                 `json:"function"`
	Status     string                 `json:"status"`
	StartTime  int64                  `json:"start_time"`
	DurationNS int64                  `json:"duration_ns"`
	Attrs      map[string]interface{} `json:"attrs"`
	Steps      []Step                 `json:"steps"`
	Children   []*SpanNode            `json:"children"`
	ParentSID  string                 `json:"-"`
}

type TraceDetail struct {
	TID        string      `json:"tid"`
	Name       string      `json:"name"`
	Status     string      `json:"status"`
	StartTime  int64       `json:"start_time"`
	DurationNS int64       `json:"duration_ns"`
	SpanCount  int         `json:"span_count"`
	ErrorCount int         `json:"error_count"`
	Tree       []*SpanNode `json:"tree,omitempty"`
}

type Server struct {
	db    *sql.DB
	token string
}

func main() {
	dbPath := os.Getenv("DB_PATH")
	if dbPath == "" {
		dbPath = "./traces.db"
	}

	// Ensure db dir exists
	dir := filepath.Dir(dbPath)
	if dir != "." && dir != "" {
		_ = os.MkdirAll(dir, 0755)
	}

		// Connect to SQLite with WAL enabled
	db, err := sql.Open("sqlite", dbPath)
	if err != nil {
		log.Fatalf("failed to open database: %v", err)
	}
	db.SetMaxOpenConns(1)
	_, _ = db.Exec("PRAGMA journal_mode=WAL; PRAGMA synchronous=NORMAL; PRAGMA busy_timeout=5000;")
	defer db.Close()

	// Apply migrations
	runMigrations(db)

	srv := &Server{
		db:    db,
		token: os.Getenv("TRACE_TOKEN"),
	}

	retentionHoursStr := os.Getenv("RETENTION_HOURS")
	retentionHours := 48 // Default to 48 hours (2 days)
	if retentionHoursStr != "" {
		if val, err := strconv.Atoi(retentionHoursStr); err == nil {
			retentionHours = val
		}
	}
	if retentionHours > 0 {
		srv.startCleanupTask(time.Duration(retentionHours) * time.Hour)
	}

	// Ingest port — configurable via INGEST_PORT (default 4318)
	ingestPort := os.Getenv("INGEST_PORT")
	if ingestPort == "" {
		ingestPort = "4318"
	}
	ingestMux := http.NewServeMux()
	ingestMux.HandleFunc("/v1/traces", srv.handleIngest)

	// Query API port — configurable via QUERY_PORT (default 4319)
	queryPort := os.Getenv("QUERY_PORT")
	if queryPort == "" {
		queryPort = "4319"
	}
	queryMux := http.NewServeMux()
	queryMux.HandleFunc("/health", srv.handleHealth)
	queryMux.HandleFunc("/traces", srv.handleTraces)
	queryMux.HandleFunc("/traces/", srv.handleSingleTraceRoute)
	queryMux.HandleFunc("/spans/", srv.handleSingleSpanRoute)
	queryMux.HandleFunc("/classes", srv.handleClasses)
	queryMux.HandleFunc("/functions", srv.handleFunctions)

	var wg sync.WaitGroup
	wg.Add(2)

	go func() {
		defer wg.Done()
		log.Printf("Starting Ingest API on :%s...", ingestPort)
		if err := http.ListenAndServe(":"+ingestPort, ingestMux); err != nil {
			log.Printf("Ingest server error: %v", err)
		}
	}()

	go func() {
		defer wg.Done()
		log.Printf("Starting Query API on :%s...", queryPort)
		if err := http.ListenAndServe(":"+queryPort, queryMux); err != nil {
			log.Printf("Query server error: %v", err)
		}
	}()

	wg.Wait()
}

func runMigrations(db *sql.DB) {
	// Look for migration file
	migrationPaths := []string{
		"./database/migrations/0001_init.sql",
		"../database/migrations/0001_init.sql",
		"/app/database/migrations/0001_init.sql",
	}

	var migrationSQL []byte
	var err error
	for _, p := range migrationPaths {
		migrationSQL, err = os.ReadFile(p)
		if err == nil {
			log.Printf("Applying migrations from %s", p)
			break
		}
	}

	if err != nil {
		// Fallback schema if migration file not found
		log.Println("Migration file not found, applying default embedded schema")
		migrationSQL = []byte(`
			CREATE TABLE IF NOT EXISTS traces (
			  tid          TEXT PRIMARY KEY,
			  name         TEXT,
			  status       TEXT,
			  start_time   INTEGER,
			  end_time     INTEGER,
			  span_count   INTEGER,
			  error_count  INTEGER
			);
			CREATE TABLE IF NOT EXISTS spans (
			  sid          TEXT PRIMARY KEY,
			  tid          TEXT,
			  parent_sid   TEXT,
			  class        TEXT,
			  function     TEXT,
			  status       TEXT,
			  start_time   INTEGER,
			  end_time     INTEGER,
			  attrs        TEXT
			);
			CREATE TABLE IF NOT EXISTS steps (
			  id           INTEGER PRIMARY KEY AUTOINCREMENT,
			  sid          TEXT,
			  tid          TEXT,
			  step         TEXT,
			  message      TEXT,
			  level        TEXT,
			  ts           INTEGER
			);
			CREATE INDEX IF NOT EXISTS idx_spans_tid ON spans(tid);
			CREATE INDEX IF NOT EXISTS idx_spans_class ON spans(class);
			CREATE INDEX IF NOT EXISTS idx_spans_function ON spans(function);
			CREATE INDEX IF NOT EXISTS idx_spans_parent_sid ON spans(parent_sid);
			CREATE INDEX IF NOT EXISTS idx_steps_sid ON steps(sid);
			CREATE INDEX IF NOT EXISTS idx_steps_tid ON steps(tid);
			CREATE INDEX IF NOT EXISTS idx_traces_start_time ON traces(start_time);
			CREATE INDEX IF NOT EXISTS idx_traces_status ON traces(status);
		`)
	}

	_, err = db.Exec(string(migrationSQL))
	if err != nil {
		log.Fatalf("failed to apply migrations: %v", err)
	}
	log.Println("Migrations applied successfully.")
}

func (s *Server) startCleanupTask(retention time.Duration) {
	// Run cleanup check every 15 minutes
	ticker := time.NewTicker(15 * time.Minute)
	go func() {
		for range ticker.C {
			cutoff := time.Now().Add(-retention).UnixNano()
			log.Printf("[Retention] Running cleanup for data older than %v...", retention)

			tx, err := s.db.Begin()
			if err != nil {
				log.Printf("[Retention] Failed to start transaction: %v", err)
				continue
			}

			// Delete steps associated with expired traces
			_, err = tx.Exec("DELETE FROM steps WHERE tid IN (SELECT tid FROM traces WHERE start_time < ?)", cutoff)
			if err != nil {
				tx.Rollback()
				log.Printf("[Retention] Failed to delete steps: %v", err)
				continue
			}

			// Delete spans associated with expired traces
			_, err = tx.Exec("DELETE FROM spans WHERE tid IN (SELECT tid FROM traces WHERE start_time < ?)", cutoff)
			if err != nil {
				tx.Rollback()
				log.Printf("[Retention] Failed to delete spans: %v", err)
				continue
			}

			// Delete expired traces themselves
			res, err := tx.Exec("DELETE FROM traces WHERE start_time < ?", cutoff)
			if err != nil {
				tx.Rollback()
				log.Printf("[Retention] Failed to delete traces: %v", err)
				continue
			}

			if err := tx.Commit(); err != nil {
				log.Printf("[Retention] Failed to commit cleanup: %v", err)
				continue
			}

			rowsAffected, _ := res.RowsAffected()
			if rowsAffected > 0 {
				log.Printf("[Retention] Cleanup successful. Removed %d expired traces.", rowsAffected)
			}
		}
	}()
}

func (s *Server) authenticate(w http.ResponseWriter, r *http.Request) bool {
	if s.token == "" {
		return true
	}
	authHeader := r.Header.Get("Authorization")
	if !strings.HasPrefix(authHeader, "Bearer ") {
		http.Error(w, `{"error": "Unauthorized"}`, http.StatusUnauthorized)
		return false
	}
	token := strings.TrimPrefix(authHeader, "Bearer ")
	if token != s.token {
		http.Error(w, `{"error": "Unauthorized"}`, http.StatusUnauthorized)
		return false
	}
	return true
}

func (s *Server) handleIngest(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, `{"error": "Method Not Allowed"}`, http.StatusMethodNotAllowed)
		return
	}
	if !s.authenticate(w, r) {
		return
	}

	body, err := io.ReadAll(r.Body)
	if err != nil {
		http.Error(w, err.Error(), http.StatusBadRequest)
		return
	}

	var payload OtlpPayload
	contentType := r.Header.Get("Content-Type")
	if contentType == "application/x-protobuf" {
		var req coltracepb.ExportTraceServiceRequest
		if err := proto.Unmarshal(body, &req); err != nil {
			http.Error(w, err.Error(), http.StatusBadRequest)
			return
		}
		payload = convertProtoToOtlpPayload(&req)
	} else {
		if err := json.Unmarshal(body, &payload); err != nil {
			http.Error(w, err.Error(), http.StatusBadRequest)
			return
		}
	}

	tx, err := s.db.Begin()
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}
	defer tx.Rollback()

	for _, resourceSpan := range payload.ResourceSpans {
		for _, scopeSpan := range resourceSpan.ScopeSpans {
			for _, span := range scopeSpan.Spans {
				// Parse timestamps
				startTime, _ := strconv.ParseInt(span.StartTimeUnixNano, 10, 64)
				endTime, _ := strconv.ParseInt(span.EndTimeUnixNano, 10, 64)

				// Find attributes
				var class, function string
				attrsMap := make(map[string]interface{})
				for _, attr := range span.Attributes {
					val := attr.Value.StringValue
					if val == "" && attr.Value.IntValue != "" {
						val = attr.Value.IntValue
					}
					if attr.Key == "code.namespace" {
						class = val
					} else if attr.Key == "code.function" {
						function = val
					} else {
						attrsMap[attr.Key] = val
					}
				}

				attrsJSON, _ := json.Marshal(attrsMap)

				// Determine status
				status := "unset"
				if span.Status != nil {
					if span.Status.Code == 2 { // StatusCode Error
						status = "error"
					} else if span.Status.Code == 1 { // StatusCode Ok
						status = "ok"
					}
				}

				parentSpanID := span.ParentSpanID
				if parentSpanID == "0000000000000000" {
					parentSpanID = ""
				}

				// Insert/replace span
				_, err = tx.Exec(`
					INSERT INTO spans (sid, tid, parent_sid, class, function, status, start_time, end_time, attrs)
					VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
					ON CONFLICT(sid) DO UPDATE SET
						parent_sid=excluded.parent_sid,
						class=excluded.class,
						function=excluded.function,
						status=excluded.status,
						start_time=excluded.start_time,
						end_time=excluded.end_time,
						attrs=excluded.attrs
				`, span.SpanID, span.TraceID, nilOrString(parentSpanID), class, function, status, startTime, endTime, string(attrsJSON))
				if err != nil {
					http.Error(w, err.Error(), http.StatusInternalServerError)
					return
				}

				// Insert steps/events
				for _, event := range span.Events {
					evtTime, _ := strconv.ParseInt(event.TimeUnixNano, 10, 64)
					var message, level string
					level = "info" // Default level
					for _, attr := range event.Attributes {
						val := attr.Value.StringValue
						if attr.Key == "message" {
							message = val
						} else if attr.Key == "level" {
							level = val
						}
					}

					_, err = tx.Exec(`
						INSERT INTO steps (sid, tid, step, message, level, ts)
						VALUES (?, ?, ?, ?, ?, ?)
					`, span.SpanID, span.TraceID, event.Name, message, level, evtTime)
					if err != nil {
						http.Error(w, err.Error(), http.StatusInternalServerError)
						return
					}
				}

				// Upsert Trace record summary
				// Find existing trace counts or start them
				var existingTid string
				var existingStart, existingEnd int64
				err = tx.QueryRow("SELECT tid, start_time, end_time FROM traces WHERE tid = ?", span.TraceID).Scan(&existingTid, &existingStart, &existingEnd)
				if err == sql.ErrNoRows {
					// Insert fresh
					_, err = tx.Exec(`
						INSERT INTO traces (tid, name, status, start_time, end_time, span_count, error_count)
						VALUES (?, ?, ?, ?, ?, 1, ?)
					`, span.TraceID, span.Name, getTraceStatus(status), startTime, endTime, errVal(status))
				} else if err == nil {
					// Update existing counts and bounds
					newStart := existingStart
					if startTime < existingStart || existingStart == 0 {
						newStart = startTime
					}
					newEnd := existingEnd
					if endTime > existingEnd {
						newEnd = endTime
					}
					_, err = tx.Exec(`
						UPDATE traces
						SET start_time = ?, end_time = ?,
						    span_count = span_count + 1,
						    error_count = error_count + ?,
						    status = ?,
						    name = CASE WHEN ? = '' THEN ? ELSE name END
						WHERE tid = ?
					`, newStart, newEnd, errVal(status), getTraceStatus(status), parentSpanID, span.Name, span.TraceID)
				}
				if err != nil {
					http.Error(w, err.Error(), http.StatusInternalServerError)
					return
				}
			}
		}
	}

	if err := tx.Commit(); err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	_, _ = w.Write([]byte(`{"status": "success"}`))
}

func nilOrString(s string) interface{} {
	if s == "" {
		return nil
	}
	return s
}

func errVal(status string) int {
	if status == "error" {
		return 1
	}
	return 0
}

func getTraceStatus(status string) string {
	if status == "error" {
		return "error"
	}
	return "ok"
}

func (s *Server) handleHealth(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	_, _ = w.Write([]byte(`{"status": "ok"}`))
}

func (s *Server) handleTraces(w http.ResponseWriter, r *http.Request) {
	if !s.authenticate(w, r) {
		return
	}
	status := r.URL.Query().Get("status")
	class := r.URL.Query().Get("class")
	function := r.URL.Query().Get("function")
	fromStr := r.URL.Query().Get("from")
	toStr := r.URL.Query().Get("to")
	limitStr := r.URL.Query().Get("limit")
	offsetStr := r.URL.Query().Get("offset")

	limit := 50
	if limitStr != "" {
		if l, err := strconv.Atoi(limitStr); err == nil {
			limit = l
		}
	}

	offset := 0
	if offsetStr != "" {
		if o, err := strconv.Atoi(offsetStr); err == nil {
			offset = o
		}
	}

	query := "SELECT tid, name, status, start_time, end_time, span_count, error_count FROM traces WHERE 1=1"
	var args []interface{}

	if status != "" {
		query += " AND status = ?"
		args = append(args, status)
	}
	if class != "" {
		query += " AND tid IN (SELECT DISTINCT tid FROM spans WHERE class = ?)"
		args = append(args, class)
	}
	if function != "" {
		query += " AND tid IN (SELECT DISTINCT tid FROM spans WHERE function = ?)"
		args = append(args, function)
	}
	if fromStr != "" {
		if from, err := strconv.ParseInt(fromStr, 10, 64); err == nil {
			query += " AND start_time >= ?"
			args = append(args, from)
		}
	}
	if toStr != "" {
		if to, err := strconv.ParseInt(toStr, 10, 64); err == nil {
			query += " AND start_time <= ?"
			args = append(args, to)
		}
	}

	query += " ORDER BY start_time DESC LIMIT ? OFFSET ?"
	args = append(args, limit, offset)

	rows, err := s.db.Query(query, args...)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}
	defer rows.Close()

	var traces []TraceDetail
	for rows.Next() {
		var td TraceDetail
		var endT int64
		if err := rows.Scan(&td.TID, &td.Name, &td.Status, &td.StartTime, &endT, &td.SpanCount, &td.ErrorCount); err != nil {
			http.Error(w, err.Error(), http.StatusInternalServerError)
			return
		}
		td.DurationNS = endT - td.StartTime
		traces = append(traces, td)
	}

	// Count total
	var total int
	countQuery := "SELECT COUNT(*) FROM traces"
	_ = s.db.QueryRow(countQuery).Scan(&total)

	w.Header().Set("Content-Type", "application/json")
	_ = json.NewEncoder(w).Encode(map[string]interface{}{
		"total":  total,
		"traces": traces,
	})
}

func (s *Server) handleSingleTraceRoute(w http.ResponseWriter, r *http.Request) {
	if !s.authenticate(w, r) {
		return
	}
	// Format: /traces/:tid or /traces/:tid/spans
	parts := strings.Split(r.URL.Path, "/")
	if len(parts) < 3 {
		http.Error(w, `{"error": "Not Found"}`, http.StatusNotFound)
		return
	}
	tid := parts[2]

	if len(parts) == 4 && parts[3] == "spans" {
		s.handleFlatSpans(w, tid)
		return
	}

	s.handleTraceTree(w, tid)
}

func (s *Server) handleTraceTree(w http.ResponseWriter, tid string) {
	var td TraceDetail
	var endTime int64
	err := s.db.QueryRow("SELECT tid, name, status, start_time, end_time, span_count, error_count FROM traces WHERE tid = ?", tid).
		Scan(&td.TID, &td.Name, &td.Status, &td.StartTime, &endTime, &td.SpanCount, &td.ErrorCount)
	if err == sql.ErrNoRows {
		http.Error(w, `{"error": "Trace Not Found"}`, http.StatusNotFound)
		return
	} else if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}
	td.DurationNS = endTime - td.StartTime

	// Get all spans
	rows, err := s.db.Query("SELECT sid, parent_sid, class, function, status, start_time, end_time, attrs FROM spans WHERE tid = ?", tid)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}
	defer rows.Close()

	var nodes []*SpanNode
	nodesMap := make(map[string]*SpanNode)

	for rows.Next() {
		var n SpanNode
		var parentSid sql.NullString
		var endT int64
		var attrsStr string
		if err := rows.Scan(&n.SID, &parentSid, &n.Class, &n.Function, &n.Status, &n.StartTime, &endT, &attrsStr); err != nil {
			http.Error(w, err.Error(), http.StatusInternalServerError)
			return
		}
		n.DurationNS = endT - n.StartTime
		if parentSid.Valid {
			n.ParentSID = parentSid.String
		}

		_ = json.Unmarshal([]byte(attrsStr), &n.Attrs)
		nodes = append(nodes, &n)
		nodesMap[n.SID] = &n
	}

	// Fetch all steps for the trace
	stepRows, err := s.db.Query("SELECT sid, step, message, level, ts FROM steps WHERE tid = ? ORDER BY ts ASC", tid)
	if err == nil {
		defer stepRows.Close()
		for stepRows.Next() {
			var sid string
			var st Step
			if err := stepRows.Scan(&sid, &st.Step, &st.Message, &st.Level, &st.TS); err == nil {
				if node, ok := nodesMap[sid]; ok {
					node.Steps = append(node.Steps, st)
				}
			}
		}
	}

	// Assemble tree
	var tree []*SpanNode
	for _, n := range nodes {
		if n.ParentSID == "" {
			tree = append(tree, n)
		} else {
			if parent, ok := nodesMap[n.ParentSID]; ok {
				parent.Children = append(parent.Children, n)
			} else {
				// Dangling parent context
				tree = append(tree, n)
			}
		}
	}

	td.Tree = tree
	w.Header().Set("Content-Type", "application/json")
	_ = json.NewEncoder(w).Encode(td)
}

func (s *Server) handleFlatSpans(w http.ResponseWriter, tid string) {
	rows, err := s.db.Query("SELECT sid, parent_sid, class, function, status, start_time, end_time, attrs FROM spans WHERE tid = ?", tid)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}
	defer rows.Close()

	var spans []map[string]interface{}
	for rows.Next() {
		var sid, parentSid, class, function, status, attrsStr string
		var startT, endT int64
		var pSid sql.NullString
		if err := rows.Scan(&sid, &pSid, &class, &function, &status, &startT, &endT, &attrsStr); err == nil {
			if pSid.Valid {
				parentSid = pSid.String
			}
			var attrs map[string]interface{}
			_ = json.Unmarshal([]byte(attrsStr), &attrs)
			spans = append(spans, map[string]interface{}{
				"sid":         sid,
				"parent_sid":  parentSid,
				"class":       class,
				"function":    function,
				"status":      status,
				"start_time":  startT,
				"duration_ns": endT - startT,
				"attrs":       attrs,
			})
		}
	}

	w.Header().Set("Content-Type", "application/json")
	_ = json.NewEncoder(w).Encode(spans)
}

func (s *Server) handleSingleSpanRoute(w http.ResponseWriter, r *http.Request) {
	if !s.authenticate(w, r) {
		return
	}
	// Format: /spans/:sid
	parts := strings.Split(r.URL.Path, "/")
	if len(parts) < 3 {
		http.Error(w, `{"error": "Not Found"}`, http.StatusNotFound)
		return
	}
	sid := parts[2]

	var n SpanNode
	var parentSid sql.NullString
	var endT int64
	var attrsStr string
	err := s.db.QueryRow("SELECT sid, parent_sid, class, function, status, start_time, end_time, attrs FROM spans WHERE sid = ?", sid).
		Scan(&n.SID, &parentSid, &n.Class, &n.Function, &n.Status, &n.StartTime, &endT, &attrsStr)
	if err == sql.ErrNoRows {
		http.Error(w, `{"error": "Span Not Found"}`, http.StatusNotFound)
		return
	} else if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}
	n.DurationNS = endT - n.StartTime
	if parentSid.Valid {
		n.ParentSID = parentSid.String
	}
	_ = json.Unmarshal([]byte(attrsStr), &n.Attrs)

	// Fetch steps for this span
	stepRows, err := s.db.Query("SELECT step, message, level, ts FROM steps WHERE sid = ? ORDER BY ts ASC", sid)
	if err == nil {
		defer stepRows.Close()
		for stepRows.Next() {
			var st Step
			if err := stepRows.Scan(&st.Step, &st.Message, &st.Level, &st.TS); err == nil {
				n.Steps = append(n.Steps, st)
			}
		}
	}

	// Fetch immediate children
	childRows, err := s.db.Query("SELECT sid, class, function, status, start_time, end_time, attrs FROM spans WHERE parent_sid = ?", sid)
	if err == nil {
		defer childRows.Close()
		for childRows.Next() {
			var child SpanNode
			var childEnd int64
			var childAttrs string
			if err := childRows.Scan(&child.SID, &child.Class, &child.Function, &child.Status, &child.StartTime, &childEnd, &childAttrs); err == nil {
				child.DurationNS = childEnd - child.StartTime
				_ = json.Unmarshal([]byte(childAttrs), &child.Attrs)
				n.Children = append(n.Children, &child)
			}
		}
	}

	w.Header().Set("Content-Type", "application/json")
	_ = json.NewEncoder(w).Encode(n)
}

func (s *Server) handleClasses(w http.ResponseWriter, r *http.Request) {
	if !s.authenticate(w, r) {
		return
	}
	rows, err := s.db.Query("SELECT DISTINCT class FROM spans WHERE class IS NOT NULL AND class != '' ORDER BY class")
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}
	defer rows.Close()

	classes := []string{}
	for rows.Next() {
		var class string
		if err := rows.Scan(&class); err == nil {
			classes = append(classes, class)
		}
	}

	w.Header().Set("Content-Type", "application/json")
	_ = json.NewEncoder(w).Encode(classes)
}

func (s *Server) handleFunctions(w http.ResponseWriter, r *http.Request) {
	if !s.authenticate(w, r) {
		return
	}
	class := r.URL.Query().Get("class")
	query := "SELECT DISTINCT function FROM spans WHERE function IS NOT NULL AND function != ''"
	var args []interface{}
	if class != "" {
		query += " AND class = ?"
		args = append(args, class)
	}
	query += " ORDER BY function"

	rows, err := s.db.Query(query, args...)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}
	defer rows.Close()

	funcs := []string{}
	for rows.Next() {
		var f string
		if err := rows.Scan(&f); err == nil {
			funcs = append(funcs, f)
		}
	}

	w.Header().Set("Content-Type", "application/json")
	_ = json.NewEncoder(w).Encode(funcs)
}

func convertProtoToOtlpPayload(req *coltracepb.ExportTraceServiceRequest) OtlpPayload {
	var payload OtlpPayload
	for _, rs := range req.ResourceSpans {
		var resourceSpans ResourceSpans
		if rs.Resource != nil {
			var resource Resource
			for _, attr := range rs.Resource.Attributes {
				valHolder := ValueHolder{}
				if attr.Value != nil {
					if attr.Value.GetStringValue() != "" {
						valHolder.StringValue = attr.Value.GetStringValue()
					} else if attr.Value.GetIntValue() != 0 {
						valHolder.IntValue = strconv.FormatInt(attr.Value.GetIntValue(), 10)
					}
				}
				resource.Attributes = append(resource.Attributes, KeyValue{
					Key:   attr.Key,
					Value: valHolder,
				})
			}
			resourceSpans.Resource = &resource
		}

		for _, ss := range rs.ScopeSpans {
			var scopeSpans ScopeSpans
			for _, span := range ss.Spans {
				var otlpSpan OtlpSpan
				otlpSpan.TraceID = hex.EncodeToString(span.TraceId)
				otlpSpan.SpanID = hex.EncodeToString(span.SpanId)
				if len(span.ParentSpanId) > 0 {
					otlpSpan.ParentSpanID = hex.EncodeToString(span.ParentSpanId)
				}
				otlpSpan.Name = span.Name
				otlpSpan.StartTimeUnixNano = strconv.FormatUint(span.StartTimeUnixNano, 10)
				otlpSpan.EndTimeUnixNano = strconv.FormatUint(span.EndTimeUnixNano, 10)

				for _, attr := range span.Attributes {
					valHolder := ValueHolder{}
					if attr.Value != nil {
						valHolder.StringValue = attr.Value.GetStringValue()
						if valHolder.StringValue == "" && attr.Value.GetIntValue() != 0 {
							valHolder.IntValue = strconv.FormatInt(attr.Value.GetIntValue(), 10)
						}
					}
					otlpSpan.Attributes = append(otlpSpan.Attributes, KeyValue{
						Key:   attr.Key,
						Value: valHolder,
					})
				}

				for _, event := range span.Events {
					var otlpEvent OtlpEvent
					otlpEvent.TimeUnixNano = strconv.FormatUint(event.TimeUnixNano, 10)
					otlpEvent.Name = event.Name
					for _, attr := range event.Attributes {
						valHolder := ValueHolder{}
						if attr.Value != nil {
							valHolder.StringValue = attr.Value.GetStringValue()
							if valHolder.StringValue == "" && attr.Value.GetIntValue() != 0 {
								valHolder.IntValue = strconv.FormatInt(attr.Value.GetIntValue(), 10)
							}
						}
						otlpEvent.Attributes = append(otlpEvent.Attributes, KeyValue{
							Key:   attr.Key,
							Value: valHolder,
						})
					}
					otlpSpan.Events = append(otlpSpan.Events, otlpEvent)
				}

				if span.Status != nil {
					var otlpStatus OtlpStatus
					otlpStatus.Code = int(span.Status.Code)
					otlpStatus.Message = span.Status.Message
					otlpSpan.Status = &otlpStatus
				}

				scopeSpans.Spans = append(scopeSpans.Spans, otlpSpan)
			}
			resourceSpans.ScopeSpans = append(resourceSpans.ScopeSpans, scopeSpans)
		}
		payload.ResourceSpans = append(payload.ResourceSpans, resourceSpans)
	}
	return payload
}
