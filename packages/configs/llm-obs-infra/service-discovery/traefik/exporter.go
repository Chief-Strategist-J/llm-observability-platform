package traefik

import (
	"context"
	"fmt"
	"log"
	"os"
	"path/filepath"
	"sync"
	"time"

	"github.com/llm-observability/platform/packages/configs/llm-obs-infra/service-discovery/models"
	"github.com/llm-observability/platform/packages/configs/llm-obs-infra/service-discovery/registry"
	"github.com/llm-observability/platform/packages/configs/llm-obs-infra/service-discovery/tracing"
	"gopkg.in/yaml.v3"
)

type ExporterConfig = models.ExporterConfig

var DefaultExporterConfig = models.DefaultExporterConfig

type Exporter struct {
	registry *registry.Registry
	config   ExporterConfig
	mu       sync.Mutex
}

func NewExporter(reg *registry.Registry, config ExporterConfig) *Exporter {
	if config.SyncInterval <= 0 {
		config.SyncInterval = 5 * time.Second
	}
	return &Exporter{registry: reg, config: config}
}

func (e *Exporter) Start(events chan registry.RegistryEvent) {
	log.Printf("[traefik-reconciler] started (output=%s, domain=%s, periodicSync=%s)",
		e.config.OutputPath, e.config.DefaultDomain, e.config.SyncInterval)

	e.Export()

	ticker := time.NewTicker(e.config.SyncInterval)
	defer ticker.Stop()

	for {
		select {
		case event, ok := <-events:
			if !ok {
				log.Println("[traefik-reconciler] event stream closed, relying on periodic ticker")
				events = nil
				continue
			}
			log.Printf("[traefik-reconciler] event-triggered reconciliation: %s %s/%s",
				event.Type, event.Instance.Name, event.Instance.ID)
			e.Export()
		case <-ticker.C:
			e.Export()
		}
	}
}

type traefikConfig struct {
	HTTP traefikHTTP `yaml:"http"`
}

type traefikHTTP struct {
	Routers  map[string]traefikRouter  `yaml:"routers,omitempty"`
	Services map[string]traefikService `yaml:"services,omitempty"`
}

type traefikRouter struct {
	Rule        string   `yaml:"rule"`
	Service     string   `yaml:"service"`
	EntryPoints []string `yaml:"entryPoints"`
	TLS         struct{} `yaml:"tls"`
	Middlewares []string `yaml:"middlewares,omitempty"`
}

type traefikService struct {
	LoadBalancer traefikLB `yaml:"loadBalancer"`
}

type traefikLB struct {
	Servers     []traefikServer     `yaml:"servers"`
	HealthCheck *traefikHealthCheck `yaml:"healthCheck,omitempty"`
}

type traefikServer struct {
	URL string `yaml:"url"`
}

type traefikHealthCheck struct {
	Path     string `yaml:"path,omitempty"`
	Interval string `yaml:"interval"`
	Timeout  string `yaml:"timeout"`
}

func (e *Exporter) Export() {
	e.mu.Lock()
	defer e.mu.Unlock()

	_, span := tracing.StartSpan(context.Background(), "traefik-reconcile")
	defer span.End()
	span.SetAttribute("output.path", e.config.OutputPath)
	span.SetAttribute("domain", e.config.DefaultDomain)

	allServices := e.registry.GetAllServices()

	cfg := traefikConfig{
		HTTP: traefikHTTP{
			Routers:  make(map[string]traefikRouter),
			Services: make(map[string]traefikService),
		},
	}

	for serviceName, instances := range allServices {
		var healthyServers []traefikServer
		var healthPath string

		for _, inst := range instances {
			if inst.Status != registry.StatusHealthy && inst.Status != registry.StatusDegraded {
				continue
			}
			healthyServers = append(healthyServers, traefikServer{URL: inst.Endpoint()})
			if inst.HealthCheck.Path != "" {
				healthPath = inst.HealthCheck.Path
			}
		}

		if len(healthyServers) == 0 {
			continue
		}

		routerKey := fmt.Sprintf("%s-discovery-router", serviceName)
		serviceKey := fmt.Sprintf("%s-discovery-svc", serviceName)

		cfg.HTTP.Routers[routerKey] = traefikRouter{
			Rule:        fmt.Sprintf("Host(`%s.%s`)", serviceName, e.config.DefaultDomain),
			Service:     serviceKey,
			EntryPoints: e.config.DefaultEntryPoints,
			Middlewares: e.config.DefaultMiddlewares,
		}

		svc := traefikService{
			LoadBalancer: traefikLB{
				Servers: healthyServers,
			},
		}

		if healthPath != "" {
			svc.LoadBalancer.HealthCheck = &traefikHealthCheck{
				Path:     healthPath,
				Interval: "10s",
				Timeout:  "3s",
			}
		}

		cfg.HTTP.Services[serviceKey] = svc
	}

	data, err := yaml.Marshal(cfg)
	if err != nil {
		log.Printf("[traefik-reconciler] marshal error: %v", err)
		span.SetAttribute("export.error", err.Error())
		return
	}

	dir := filepath.Dir(e.config.OutputPath)
	_ = os.MkdirAll(dir, 0755)

	// Atomic File Write: Write to tempfile and atomic rename to target
	tempFile := fmt.Sprintf("%s.tmp.%d", e.config.OutputPath, time.Now().UnixNano())
	if err := os.WriteFile(tempFile, data, 0644); err != nil {
		log.Printf("[traefik-reconciler] write temp file error: %v", err)
		span.SetAttribute("export.error", err.Error())
		return
	}

	if err := os.Rename(tempFile, e.config.OutputPath); err != nil {
		log.Printf("[traefik-reconciler] atomic rename error: %v", err)
		span.SetAttribute("export.error", err.Error())
		_ = os.Remove(tempFile)
		return
	}

	span.SetAttribute("exported.services", fmt.Sprintf("%d", len(cfg.HTTP.Services)))
	log.Printf("[traefik-reconciler] reconciled %d services to %s", len(cfg.HTTP.Services), e.config.OutputPath)
}
