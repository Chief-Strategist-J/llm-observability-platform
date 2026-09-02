package registry

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
