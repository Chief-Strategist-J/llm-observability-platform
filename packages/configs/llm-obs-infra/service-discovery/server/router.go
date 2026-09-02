package server

import (
	"encoding/json"
	"fmt"
	"net/http"
	"sync"
	"time"

	"github.com/llm-observability/platform/packages/configs/llm-obs-infra/service-discovery/discovery"
	"github.com/llm-observability/platform/packages/configs/llm-obs-infra/service-discovery/models"
	"github.com/llm-observability/platform/packages/configs/llm-obs-infra/service-discovery/registry"
	"github.com/llm-observability/platform/packages/configs/llm-obs-infra/service-discovery/tracing"
)

type Router struct {
	mux              *http.ServeMux
	registry         *registry.Registry
	discovery        *discovery.Discovery
	idempotencyStore map[string][]byte
	idemMu           sync.RWMutex
}

type RouteSpec struct {
	Method  string
	Path    string
	Name    string
	Handler http.HandlerFunc
}

func NewRouter(reg *registry.Registry, disc *discovery.Discovery) *Router {
	r := &Router{
		mux:              http.NewServeMux(),
		registry:         reg,
		discovery:        disc,
		idempotencyStore: make(map[string][]byte),
	}
	r.registerDataDrivenRoutes()
	return r
}

func (r *Router) ServeHTTP(w http.ResponseWriter, req *http.Request) {
	tracing.Middleware(r.mux).ServeHTTP(w, req)
}

func bindJSON[T any](req *http.Request) (T, error) {
	var target T
	err := json.NewDecoder(req.Body).Decode(&target)
	return target, err
}

func (r *Router) checkIdempotency(w http.ResponseWriter, req *http.Request) bool {
	if req.Method != http.MethodPost && req.Method != http.MethodPut && req.Method != http.MethodPatch && req.Method != http.MethodDelete {
		return false
	}
	reqCtx := tracing.GetRequestContext(req.Context())
	if reqCtx.IdempotencyKey == "" {
		return false
	}

	r.idemMu.RLock()
	cached, exists := r.idempotencyStore[reqCtx.IdempotencyKey]
	r.idemMu.RUnlock()

	if exists {
		w.Header().Set("Content-Type", "application/json")
		w.Header().Set("x-cache-hit", "true")
		w.WriteHeader(http.StatusOK)
		_, _ = w.Write(cached)
		return true
	}
	return false
}

func (r *Router) saveIdempotency(key string, payload []byte) {
	if key == "" {
		return
	}
	r.idemMu.Lock()
	defer r.idemMu.Unlock()
	r.idempotencyStore[key] = payload
}

func writeSuccess[T any](r *Router, w http.ResponseWriter, req *http.Request, status int, data T) {
	reqCtx := tracing.GetRequestContext(req.Context())
	execTime := time.Since(reqCtx.StartTime).Milliseconds()

	envelope := models.ApiResponse[T]{
		Success:    true,
		StatusCode: status,
		Data:       data,
		Meta: models.ApiMeta{
			RequestId:       reqCtx.RequestId,
			CorrelationId:   reqCtx.CorrelationId,
			CausationId:     reqCtx.CausationId,
			Timestamp:       time.Now().UTC().Format(time.RFC3339Nano),
			ExecutionTimeMs: execTime,
		},
	}

	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	payload, _ := json.Marshal(envelope)
	_, _ = w.Write(payload)

	if req.Method == http.MethodPost || req.Method == http.MethodPut || req.Method == http.MethodPatch || req.Method == http.MethodDelete {
		r.saveIdempotency(reqCtx.IdempotencyKey, payload)
	}
}

func writeError(w http.ResponseWriter, req *http.Request, status int, code string, message string, details []models.ApiErrorDetail) {
	reqCtx := tracing.GetRequestContext(req.Context())
	execTime := time.Since(reqCtx.StartTime).Milliseconds()

	envelope := models.ApiErrorResponse{
		Success:    false,
		StatusCode: status,
		Error: models.ApiErrorInfo{
			Code:    code,
			Message: message,
			Details: details,
		},
		Meta: models.ApiMeta{
			RequestId:       reqCtx.RequestId,
			CorrelationId:   reqCtx.CorrelationId,
			CausationId:     reqCtx.CausationId,
			Timestamp:       time.Now().UTC().Format(time.RFC3339Nano),
			ExecutionTimeMs: execTime,
		},
	}

	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	_ = json.NewEncoder(w).Encode(envelope)
}

func (r *Router) registerDataDrivenRoutes() {
	routes := []RouteSpec{
		{http.MethodPost, "/v1/register", "register", r.handleRegister},
		{http.MethodPost, "/v1/heartbeat", "heartbeat", r.handleHeartbeat},
		{http.MethodPost, "/v1/deregister", "deregister", r.handleDeregister},
		{http.MethodGet, "/v1/resolve", "resolve", r.handleResolve},
		{http.MethodGet, "/v1/services", "services", r.handleListServices},
		{http.MethodGet, "/v1/watch", "watch", r.handleWatch},
		{http.MethodGet, "/health", "health", r.handleHealth},
	}

	for _, spec := range routes {
		m := spec.Method
		h := spec.Handler
		r.mux.HandleFunc(spec.Path, func(w http.ResponseWriter, req *http.Request) {
			if req.Method != m {
				writeError(w, req, http.StatusMethodNotAllowed, models.ErrCodeBadRequest, "Method not allowed", nil)
				return
			}
			if r.checkIdempotency(w, req) {
				return
			}
			h(w, req)
		})
	}
}

type registerRequest struct {
	Name        string            `json:"name"`
	Host        string            `json:"host"`
	Port        int               `json:"port"`
	Protocol    string            `json:"protocol"`
	Version     string            `json:"version,omitempty"`
	Weight      int               `json:"weight,omitempty"`
	Metadata    map[string]string `json:"metadata,omitempty"`
	HealthCheck struct {
		Protocol string   `json:"protocol"`
		Path     string   `json:"path,omitempty"`
		Command  []string `json:"command,omitempty"`
	} `json:"healthCheck"`
}

type heartbeatRequest struct {
	Name       string `json:"name"`
	InstanceID string `json:"instanceId"`
}

type deregisterRequest struct {
	Name       string `json:"name"`
	InstanceID string `json:"instanceId"`
}

func (r *Router) handleRegister(w http.ResponseWriter, req *http.Request) {
	body, err := bindJSON[registerRequest](req)
	if err != nil {
		writeError(w, req, http.StatusBadRequest, models.ErrCodeBadRequest, "Malformed JSON request body: "+err.Error(), nil)
		return
	}

	var details []models.ApiErrorDetail
	if body.Name == "" {
		details = append(details, models.ApiErrorDetail{Field: "name", Issue: "Field 'name' is required and cannot be empty."})
	}
	if body.Host == "" {
		details = append(details, models.ApiErrorDetail{Field: "host", Issue: "Field 'host' is required and cannot be empty."})
	}
	if body.Port <= 0 || body.Port > 65535 {
		details = append(details, models.ApiErrorDetail{Field: "port", Issue: "Field 'port' must be a valid network port between 1 and 65535."})
	}
	if body.Protocol == "" {
		details = append(details, models.ApiErrorDetail{Field: "protocol", Issue: "Field 'protocol' is required (e.g. 'http', 'tcp')."})
	}

	if len(details) > 0 {
		writeError(w, req, http.StatusBadRequest, models.ErrCodeValidationFailed, "One or more payload validation checks failed.", details)
		return
	}

	instance := &registry.ServiceInstance{
		Name:     body.Name,
		Host:     body.Host,
		Port:     body.Port,
		Protocol: body.Protocol,
		Version:  body.Version,
		Weight:   body.Weight,
		Metadata: body.Metadata,
		HealthCheck: registry.HealthCheckSpec{
			Protocol: body.HealthCheck.Protocol,
			Path:     body.HealthCheck.Path,
			Command:  body.HealthCheck.Command,
		},
	}

	registered := r.registry.Register(instance)
	writeSuccess(r, w, req, http.StatusCreated, registered)
}

func (r *Router) handleHeartbeat(w http.ResponseWriter, req *http.Request) {
	body, err := bindJSON[heartbeatRequest](req)
	if err != nil {
		writeError(w, req, http.StatusBadRequest, models.ErrCodeBadRequest, "Malformed JSON request body: "+err.Error(), nil)
		return
	}

	var details []models.ApiErrorDetail
	if body.Name == "" {
		details = append(details, models.ApiErrorDetail{Field: "name", Issue: "Field 'name' is required."})
	}
	if body.InstanceID == "" {
		details = append(details, models.ApiErrorDetail{Field: "instanceId", Issue: "Field 'instanceId' is required."})
	}
	if len(details) > 0 {
		writeError(w, req, http.StatusBadRequest, models.ErrCodeValidationFailed, "One or more payload validation checks failed.", details)
		return
	}

	if err := r.registry.Heartbeat(body.Name, body.InstanceID); err != nil {
		writeError(w, req, http.StatusNotFound, models.ErrCodeNotFound, fmt.Sprintf("Service instance '%s/%s' not found or heartbeat expired.", body.Name, body.InstanceID), nil)
		return
	}

	writeSuccess(r, w, req, http.StatusOK, map[string]string{"status": "ok"})
}

func (r *Router) handleDeregister(w http.ResponseWriter, req *http.Request) {
	body, err := bindJSON[deregisterRequest](req)
	if err != nil {
		writeError(w, req, http.StatusBadRequest, models.ErrCodeBadRequest, "Malformed JSON request body: "+err.Error(), nil)
		return
	}

	var details []models.ApiErrorDetail
	if body.Name == "" {
		details = append(details, models.ApiErrorDetail{Field: "name", Issue: "Field 'name' is required."})
	}
	if body.InstanceID == "" {
		details = append(details, models.ApiErrorDetail{Field: "instanceId", Issue: "Field 'instanceId' is required."})
	}
	if len(details) > 0 {
		writeError(w, req, http.StatusBadRequest, models.ErrCodeValidationFailed, "One or more payload validation checks failed.", details)
		return
	}

	if err := r.registry.Deregister(body.Name, body.InstanceID); err != nil {
		writeError(w, req, http.StatusNotFound, models.ErrCodeNotFound, fmt.Sprintf("Service instance '%s/%s' not found.", body.Name, body.InstanceID), nil)
		return
	}

	writeSuccess(r, w, req, http.StatusOK, map[string]string{"status": "deregistered"})
}

type resolveResponseData struct {
	Service   string                    `json:"service"`
	Endpoint  string                    `json:"endpoint"`
	Instances []*registry.ServiceInstance `json:"instances"`
}

func (r *Router) handleResolve(w http.ResponseWriter, req *http.Request) {
	serviceName := req.URL.Query().Get("service")
	if serviceName == "" {
		writeError(w, req, http.StatusBadRequest, models.ErrCodeBadRequest, "Missing mandatory 'service' query parameter.", []models.ApiErrorDetail{
			{Field: "service", Issue: "Query parameter 'service' must be specified (e.g. ?service=ai-service)."},
		})
		return
	}

	instances, err := r.discovery.ResolveAll(serviceName)
	if err != nil {
		writeError(w, req, http.StatusServiceUnavailable, models.ErrCodeServiceUnavailable, err.Error(), nil)
		return
	}

	writeSuccess(r, w, req, http.StatusOK, resolveResponseData{
		Service:   serviceName,
		Endpoint:  instances[0].Endpoint(),
		Instances: instances,
	})
}

func (r *Router) handleListServices(w http.ResponseWriter, req *http.Request) {
	services := r.discovery.ListServices()
	writeSuccess(r, w, req, http.StatusOK, services)
}

func (r *Router) handleWatch(w http.ResponseWriter, req *http.Request) {
	serviceName := req.URL.Query().Get("service")

	flusher, ok := w.(http.Flusher)
	if !ok {
		writeError(w, req, http.StatusInternalServerError, models.ErrCodeInternalServerError, "Server Sent Events (SSE) streaming not supported.", nil)
		return
	}

	w.Header().Set("Content-Type", "text/event-stream")
	w.Header().Set("Cache-Control", "no-cache")
	w.Header().Set("Connection", "keep-alive")
	w.WriteHeader(http.StatusOK)
	flusher.Flush()

	var events chan registry.RegistryEvent
	if serviceName != "" {
		events = r.discovery.Watch(serviceName)
	} else {
		events = r.discovery.WatchAll()
	}

	ctx := req.Context()
	for {
		select {
		case <-ctx.Done():
			return
		case event, ok := <-events:
			if !ok {
				return
			}
			data, _ := json.Marshal(event)
			fmt.Fprintf(w, "event: %s\ndata: %s\n\n", event.Type.String(), data)
			flusher.Flush()
		}
	}
}

func (r *Router) handleHealth(w http.ResponseWriter, req *http.Request) {
	writeSuccess(r, w, req, http.StatusOK, map[string]interface{}{
		"status": "healthy",
		"time":   time.Now().UTC().Format(time.RFC3339Nano),
	})
}
