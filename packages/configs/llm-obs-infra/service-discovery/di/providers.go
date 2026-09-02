package di

import (
	"encoding/json"
	"log"
	"os"
	"time"

	"github.com/llm-observability/platform/packages/configs/llm-obs-infra/service-discovery/discovery"
	"github.com/llm-observability/platform/packages/configs/llm-obs-infra/service-discovery/loadbalancer"
	"github.com/llm-observability/platform/packages/configs/llm-obs-infra/service-discovery/registry"
	"github.com/llm-observability/platform/packages/configs/llm-obs-infra/service-discovery/server"
	"github.com/llm-observability/platform/packages/configs/llm-obs-infra/service-discovery/traefik"
)

type AppConfig struct {
	Server         server.ServerConfig              `json:"server"`
	Registry       registry.InstanceDefaults         `json:"registry"`
	LeaseManager   registry.LeaseManagerConfig       `json:"leaseManager"`
	HealthProber   registry.HealthProberConfig        `json:"healthProber"`
	CircuitBreaker loadbalancer.CircuitBreakerConfig  `json:"circuitBreaker"`
	LoadBalancer   struct {
		Algorithm loadbalancer.Algorithm `json:"algorithm"`
	} `json:"loadBalancer"`
	Traefik traefik.ExporterConfig `json:"traefik"`
}

var DefaultAppConfig = AppConfig{
	Server:         server.DefaultServerConfig,
	Registry:       registry.DefaultInstanceDefaults,
	LeaseManager:   registry.DefaultLeaseManagerConfig,
	HealthProber:   registry.DefaultHealthProberConfig,
	CircuitBreaker: loadbalancer.DefaultCircuitBreakerConfig,
	LoadBalancer: struct {
		Algorithm loadbalancer.Algorithm `json:"algorithm"`
	}{Algorithm: loadbalancer.AlgorithmRoundRobin},
	Traefik: traefik.DefaultExporterConfig,
}

type Container struct {
	Config         AppConfig
	Registry       *registry.Registry
	LeaseManager   *registry.LeaseManager
	HealthProber   *registry.HealthProber
	Discovery      *discovery.Discovery
	Balancer       loadbalancer.Balancer
	CBRegistry     *loadbalancer.CircuitBreakerRegistry
	Server         *server.Server
	TraefikExporter *traefik.Exporter
}

func LoadConfig(configPath string) AppConfig {
	config := DefaultAppConfig

	data, err := os.ReadFile(configPath)
	if err != nil {
		log.Printf("[di] config file not found at %s, using defaults", configPath)
		return config
	}

	if err := json.Unmarshal(data, &config); err != nil {
		log.Printf("[di] config parse error: %v, using defaults", err)
		return DefaultAppConfig
	}

	applyDurationDefaults(&config)
	return config
}

func applyDurationDefaults(config *AppConfig) {
	if config.Server.ReadTimeout == 0 {
		config.Server.ReadTimeout = 10 * time.Second
	}
	if config.Server.WriteTimeout == 0 {
		config.Server.WriteTimeout = 30 * time.Second
	}
	if config.Server.ShutdownTimeout == 0 {
		config.Server.ShutdownTimeout = 5 * time.Second
	}
}

func BuildContainer(config AppConfig) *Container {
	reg := registry.NewRegistry(config.Registry)
	lm := registry.NewLeaseManager(reg, config.LeaseManager)
	hp := registry.NewHealthProber(reg, config.HealthProber)
	disc := discovery.NewDiscovery(reg)

	balancer, err := loadbalancer.NewBalancer(config.LoadBalancer.Algorithm)
	if err != nil {
		log.Printf("[di] falling back to round_robin: %v", err)
		balancer, _ = loadbalancer.NewBalancer(loadbalancer.AlgorithmRoundRobin)
	}

	cbReg := loadbalancer.NewCircuitBreakerRegistry(config.CircuitBreaker)
	router := server.NewRouter(reg, disc)
	srv := server.NewServer(config.Server, router)
	exporter := traefik.NewExporter(reg, config.Traefik)

	return &Container{
		Config:          config,
		Registry:        reg,
		LeaseManager:    lm,
		HealthProber:    hp,
		Discovery:       disc,
		Balancer:        balancer,
		CBRegistry:      cbReg,
		Server:          srv,
		TraefikExporter: exporter,
	}
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

func LoadSeedCatalog(catalogPath string, reg *registry.Registry) {
	data, err := os.ReadFile(catalogPath)
	if err != nil {
		log.Printf("[di] seed catalog not found at %s, skipping", catalogPath)
		return
	}

	var catalog SeedCatalog
	if err := json.Unmarshal(data, &catalog); err != nil {
		log.Printf("[di] seed catalog parse error: %v", err)
		return
	}

	for _, svc := range catalog.Services {
		reg.Register(&registry.ServiceInstance{
			Name:     svc.Name,
			Host:     svc.Host,
			Port:     svc.Port,
			Protocol: svc.Protocol,
			HealthCheck: registry.HealthCheckSpec{
				Protocol: svc.HealthCheck.Protocol,
				Path:     svc.HealthCheck.Path,
			},
			Metadata: map[string]string{"source": "seed-catalog"},
		})
	}

	log.Printf("[di] loaded %d seed services from %s", len(catalog.Services), catalogPath)
}
