package registry

import (
	"github.com/llm-observability/platform/packages/configs/llm-obs-infra/service-discovery/models"
)

type HealthStatus = models.HealthStatus

const (
	StatusHealthy   = models.StatusHealthy
	StatusDegraded  = models.StatusDegraded
	StatusUnhealthy = models.StatusUnhealthy
	StatusDead      = models.StatusDead
)

type HealthCheckSpec = models.HealthCheckSpec
type ServiceInstance = models.ServiceInstance
type EventType = models.EventType

const (
	EventRegistered       = models.EventRegistered
	EventDeregistered     = models.EventDeregistered
	EventStatusChanged    = models.EventStatusChanged
	EventHeartbeatExpired = models.EventHeartbeatExpired
	EventEvicted          = models.EventEvicted
)

type RegistryEvent = models.RegistryEvent
type InstanceDefaults = models.InstanceDefaults
type LeaseManagerConfig = models.LeaseManagerConfig
type HealthProberConfig = models.HealthProberConfig

var (
	DefaultInstanceDefaults   = models.DefaultInstanceDefaults
	DefaultLeaseManagerConfig = models.DefaultLeaseManagerConfig
	DefaultHealthProberConfig = models.DefaultHealthProberConfig
)
