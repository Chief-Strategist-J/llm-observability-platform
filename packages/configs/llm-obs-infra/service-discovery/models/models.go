package models

import (
	"fmt"
	"time"
)

type HealthStatus int

const (
	StatusHealthy HealthStatus = iota
	StatusDegraded
	StatusUnhealthy
	StatusDead
)

var healthStatusNames = map[HealthStatus]string{
	StatusHealthy:   "HEALTHY",
	StatusDegraded:  "DEGRADED",
	StatusUnhealthy: "UNHEALTHY",
	StatusDead:      "DEAD",
}

func (s HealthStatus) String() string {
	if name, ok := healthStatusNames[s]; ok {
		return name
	}
	return "UNKNOWN"
}

type HealthCheckSpec struct {
	Protocol         string        `json:"protocol"`
	Path             string        `json:"path,omitempty"`
	Command          []string      `json:"command,omitempty"`
	Interval         time.Duration `json:"interval,omitempty"`
	Timeout          time.Duration `json:"timeout,omitempty"`
	SuccessThreshold int           `json:"successThreshold,omitempty"`
	FailureThreshold int           `json:"failureThreshold,omitempty"`
}

type ServiceInstance struct {
	ID                   string            `json:"id"`
	Name                 string            `json:"name"`
	Host                 string            `json:"host"`
	Port                 int               `json:"port"`
	Protocol             string            `json:"protocol"`
	Version              string            `json:"version,omitempty"`
	Weight               int               `json:"weight,omitempty"`
	Status               HealthStatus      `json:"status"`
	HealthCheck          HealthCheckSpec   `json:"healthCheck"`
	Metadata             map[string]string `json:"metadata,omitempty"`
	RegisteredAt         time.Time         `json:"registeredAt"`
	LastHeartbeat        time.Time         `json:"lastHeartbeat"`
	LastProbeAt          time.Time         `json:"lastProbeAt,omitempty"`
	LastProbeErr         string            `json:"lastProbeErr,omitempty"`
	ConsecutiveFails     int               `json:"consecutiveFails"`
	ConsecutiveSuccesses int               `json:"consecutiveSuccesses"`
}

func (si *ServiceInstance) Endpoint() string {
	return fmt.Sprintf("%s://%s:%d", si.Protocol, si.Host, si.Port)
}

type EventType int

const (
	EventRegistered EventType = iota
	EventDeregistered
	EventStatusChanged
	EventHeartbeatExpired
	EventWeightUpdated
)

var eventTypeNames = map[EventType]string{
	EventRegistered:       "REGISTERED",
	EventDeregistered:     "DEREGISTERED",
	EventStatusChanged:    "STATUS_CHANGED",
	EventHeartbeatExpired: "HEARTBEAT_EXPIRED",
	EventWeightUpdated:    "WEIGHT_UPDATED",
}

func (e EventType) String() string {
	if name, ok := eventTypeNames[e]; ok {
		return name
	}
	return "UNKNOWN"
}

type RegistryEvent struct {
	Type     EventType        `json:"type"`
	Instance *ServiceInstance `json:"instance"`
	Time     time.Time        `json:"time"`
}

type InstanceDefaults struct {
	Weight              int           `json:"weight"`
	HealthCheckInterval time.Duration `json:"healthCheckInterval"`
	HealthCheckTimeout  time.Duration `json:"healthCheckTimeout"`
}

var DefaultInstanceDefaults = InstanceDefaults{
	Weight:              100,
	HealthCheckInterval: 5 * time.Second,
	HealthCheckTimeout:  2 * time.Second,
}

type LeaseManagerConfig struct {
	SweepInterval time.Duration `json:"sweepInterval"`
	HeartbeatTTL  time.Duration `json:"heartbeatTTL"`
	EvictionTTL   time.Duration `json:"evictionTTL"`
}

var DefaultLeaseManagerConfig = LeaseManagerConfig{
	SweepInterval: 3 * time.Second,
	HeartbeatTTL:  15 * time.Second,
	EvictionTTL:   60 * time.Second,
}

type HealthProberConfig struct {
	ProbeInterval    time.Duration `json:"probeInterval"`
	MaxConcurrent    int           `json:"maxConcurrent"`
	DefaultSuccessTh int           `json:"defaultSuccessThreshold"`
	DefaultFailureTh int           `json:"defaultFailureThreshold"`
}

var DefaultHealthProberConfig = HealthProberConfig{
	ProbeInterval:    5 * time.Second,
	MaxConcurrent:    10,
	DefaultSuccessTh: 2,
	DefaultFailureTh: 3,
}

type CircuitState int

const (
	CircuitClosed CircuitState = iota
	CircuitOpen
	CircuitHalfOpen
)

var circuitStateNames = map[CircuitState]string{
	CircuitClosed:   "CLOSED",
	CircuitOpen:     "OPEN",
	CircuitHalfOpen: "HALF_OPEN",
}

func (s CircuitState) String() string {
	if name, ok := circuitStateNames[s]; ok {
		return name
	}
	return "UNKNOWN"
}

type CircuitBreakerConfig struct {
	FailureThreshold int           `json:"failureThreshold"`
	CooldownDuration time.Duration `json:"cooldownDuration"`
	HalfOpenMaxCalls int           `json:"halfOpenMaxCalls"`
}

var DefaultCircuitBreakerConfig = CircuitBreakerConfig{
	FailureThreshold: 5,
	CooldownDuration: 30 * time.Second,
	HalfOpenMaxCalls: 1,
}

type ExporterConfig struct {
	OutputPath         string   `json:"outputPath"`
	DefaultDomain      string   `json:"defaultDomain"`
	DefaultEntryPoints []string `json:"defaultEntryPoints"`
	DefaultMiddlewares []string `json:"defaultMiddlewares"`
}

var DefaultExporterConfig = ExporterConfig{
	OutputPath:         "/etc/traefik/dynamic/discovery.yml",
	DefaultDomain:      "llmobs.local",
	DefaultEntryPoints: []string{"websecure"},
	DefaultMiddlewares: []string{"security-headers@file", "rate-limit@file"},
}

type ServerConfig struct {
	Addr            string        `json:"addr"`
	ReadTimeout     time.Duration `json:"readTimeout"`
	WriteTimeout    time.Duration `json:"writeTimeout"`
	ShutdownTimeout time.Duration `json:"shutdownTimeout"`
}

var DefaultServerConfig = ServerConfig{
	Addr:            ":31426",
	ReadTimeout:     10 * time.Second,
	WriteTimeout:    30 * time.Second,
	ShutdownTimeout: 5 * time.Second,
}

type AppConfig struct {
	Server         ServerConfig         `json:"server"`
	Registry       InstanceDefaults     `json:"registry"`
	LeaseManager   LeaseManagerConfig   `json:"leaseManager"`
	HealthProber   HealthProberConfig   `json:"healthProber"`
	CircuitBreaker CircuitBreakerConfig `json:"circuitBreaker"`
	LoadBalancer   struct {
		Algorithm string `json:"algorithm"`
	} `json:"loadBalancer"`
	Traefik ExporterConfig `json:"traefik"`
}

var DefaultAppConfig = AppConfig{
	Server:         DefaultServerConfig,
	Registry:       DefaultInstanceDefaults,
	LeaseManager:   DefaultLeaseManagerConfig,
	HealthProber:   DefaultHealthProberConfig,
	CircuitBreaker: DefaultCircuitBreakerConfig,
	LoadBalancer: struct {
		Algorithm string `json:"algorithm"`
	}{Algorithm: "round_robin"},
	Traefik: DefaultExporterConfig,
}

type SeedService struct {
	Name        string `json:"name"`
	Host        string `json:"host"`
	Port        int    `json:"port"`
	Protocol    string `json:"protocol"`
	HealthCheck struct {
		Protocol string `json:"protocol"`
		Path     string `json:"path,omitempty"`
	} `json:"healthCheck"`
}

type SeedCatalog struct {
	Services []SeedService `json:"services"`
}

// Standardized API Envelopes per policies/rules/folderStructure/api-request-response-structure.md

type ApiMeta struct {
	RequestId       string `json:"requestId"`
	CorrelationId   string `json:"correlationId"`
	CausationId     string `json:"causationId"`
	Timestamp       string `json:"timestamp"`
	ExecutionTimeMs int64  `json:"executionTimeMs"`
}

type ApiResponse[T any] struct {
	Success    bool    `json:"success"`
	StatusCode int     `json:"statusCode"`
	Data       T       `json:"data"`
	Meta       ApiMeta `json:"meta"`
}

type ApiErrorDetail struct {
	Field string `json:"field,omitempty"`
	Issue string `json:"issue"`
}

type ApiErrorInfo struct {
	Code    string           `json:"code"`
	Message string           `json:"message"`
	Details []ApiErrorDetail `json:"details,omitempty"`
}

type ApiErrorResponse struct {
	Success    bool         `json:"success"`
	StatusCode int          `json:"statusCode"`
	Error      ApiErrorInfo `json:"error"`
	Meta       ApiMeta      `json:"meta"`
}

// Canonical Error Code Constants
const (
	ErrCodeBadRequest         = "BAD_REQUEST"
	ErrCodeValidationFailed   = "VALIDATION_FAILED"
	ErrCodeUnauthenticated   = "UNAUTHENTICATED"
	ErrCodeForbidden          = "FORBIDDEN"
	ErrCodeNotFound           = "NOT_FOUND"
	ErrCodeConflict           = "CONFLICT"
	ErrCodeUnprocessable      = "UNPROCESSABLE_ENTITY"
	ErrCodeTooManyRequests    = "TOO_MANY_REQUESTS"
	ErrCodeInternalServerError = "INTERNAL_SERVER_ERROR"
	ErrCodeServiceUnavailable = "SERVICE_UNAVAILABLE"
)
