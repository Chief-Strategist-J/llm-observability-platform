package server

import (
	"encoding/json"
	"fmt"
	"net/http"
	"time"

	"github.com/llm-observability/platform/packages/configs/llm-obs-infra/service-discovery/discovery"
	"github.com/llm-observability/platform/packages/configs/llm-obs-infra/service-discovery/registry"
)

type Router struct {
	mux       *http.ServeMux
	registry  *registry.Registry
	discovery *discovery.Discovery
}

func NewRouter(reg *registry.Registry, disc *discovery.Discovery) *Router {
	r := &Router{
		mux:       http.NewServeMux(),
		registry:  reg,
		discovery: disc,
	}
	r.registerRoutes()
	return r
}

func (r *Router) ServeHTTP(w http.ResponseWriter, req *http.Request) {
	r.mux.ServeHTTP(w, req)
}

type routeDef struct {
	method  string
	path    string
	handler http.HandlerFunc
}

func (r *Router) registerRoutes() {
	routes := []routeDef{
		{http.MethodPost, "/v1/register", r.handleRegister},
		{http.MethodPost, "/v1/heartbeat", r.handleHeartbeat},
		{http.MethodPost, "/v1/deregister", r.handleDeregister},
		{http.MethodGet, "/v1/resolve", r.handleResolve},
		{http.MethodGet, "/v1/services", r.handleListServices},
		{http.MethodGet, "/v1/watch", r.handleWatch},
		{http.MethodGet, "/health", r.handleHealth},
	}

	for _, route := range routes {
		m := route.method
		h := route.handler
		r.mux.HandleFunc(route.path, func(w http.ResponseWriter, req *http.Request) {
			if req.Method != m {
				writeJSON(w, http.StatusMethodNotAllowed, map[string]string{"error": "method not allowed"})
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
		Protocol string `json:"protocol"`
		Path     string `json:"path,omitempty"`
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
	var body registerRequest
	if err := json.NewDecoder(req.Body).Decode(&body); err != nil {
		writeJSON(w, http.StatusBadRequest, map[string]string{"error": err.Error()})
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
		},
	}

	registered := r.registry.Register(instance)
	writeJSON(w, http.StatusCreated, registered)
}

func (r *Router) handleHeartbeat(w http.ResponseWriter, req *http.Request) {
	var body heartbeatRequest
	if err := json.NewDecoder(req.Body).Decode(&body); err != nil {
		writeJSON(w, http.StatusBadRequest, map[string]string{"error": err.Error()})
		return
	}

	if err := r.registry.Heartbeat(body.Name, body.InstanceID); err != nil {
		writeJSON(w, http.StatusNotFound, map[string]string{"error": err.Error()})
		return
	}

	writeJSON(w, http.StatusOK, map[string]string{"status": "ok"})
}

func (r *Router) handleDeregister(w http.ResponseWriter, req *http.Request) {
	var body deregisterRequest
	if err := json.NewDecoder(req.Body).Decode(&body); err != nil {
		writeJSON(w, http.StatusBadRequest, map[string]string{"error": err.Error()})
		return
	}

	if err := r.registry.Deregister(body.Name, body.InstanceID); err != nil {
		writeJSON(w, http.StatusNotFound, map[string]string{"error": err.Error()})
		return
	}

	writeJSON(w, http.StatusOK, map[string]string{"status": "deregistered"})
}

func (r *Router) handleResolve(w http.ResponseWriter, req *http.Request) {
	serviceName := req.URL.Query().Get("service")
	if serviceName == "" {
		writeJSON(w, http.StatusBadRequest, map[string]string{"error": "missing 'service' query parameter"})
		return
	}

	instances, err := r.discovery.ResolveAll(serviceName)
	if err != nil {
		writeJSON(w, http.StatusServiceUnavailable, map[string]string{"error": err.Error()})
		return
	}

	writeJSON(w, http.StatusOK, map[string]interface{}{
		"service":   serviceName,
		"instances": instances,
		"endpoint":  instances[0].Endpoint(),
	})
}

func (r *Router) handleListServices(w http.ResponseWriter, _ *http.Request) {
	services := r.discovery.ListServices()
	writeJSON(w, http.StatusOK, services)
}

func (r *Router) handleWatch(w http.ResponseWriter, req *http.Request) {
	serviceName := req.URL.Query().Get("service")

	flusher, ok := w.(http.Flusher)
	if !ok {
		writeJSON(w, http.StatusInternalServerError, map[string]string{"error": "streaming not supported"})
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

func (r *Router) handleHealth(w http.ResponseWriter, _ *http.Request) {
	writeJSON(w, http.StatusOK, map[string]interface{}{
		"status": "healthy",
		"time":   time.Now().UTC(),
	})
}

func writeJSON(w http.ResponseWriter, status int, data interface{}) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	json.NewEncoder(w).Encode(data)
}
