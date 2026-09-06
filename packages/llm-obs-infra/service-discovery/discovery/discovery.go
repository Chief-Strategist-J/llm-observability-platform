package discovery

import (
	"context"
	"fmt"
	"strings"
	"sync"

	"github.com/llm-observability/platform/packages/configs/llm-obs-infra/service-discovery/registry"
	"github.com/llm-observability/platform/packages/configs/llm-obs-infra/service-discovery/tracing"
)

type Discovery struct {
	registry *registry.Registry
	lkgCache map[string][]*registry.ServiceInstance
	lkgMu    sync.RWMutex
}

func NewDiscovery(reg *registry.Registry) *Discovery {
	return &Discovery{
		registry: reg,
		lkgCache: make(map[string][]*registry.ServiceInstance),
	}
}

func (d *Discovery) Resolve(serviceName string) (*registry.ServiceInstance, error) {
	_, span := tracing.StartSpan(context.Background(), "discovery.resolve")
	defer span.End()
	span.SetAttribute("service.name", serviceName)

	healthy := d.registry.GetHealthy(serviceName)
	if len(healthy) == 0 {
		err := d.buildDiagnosticError(serviceName)
		span.SetAttribute("resolve.error", err.Error())
		return nil, err
	}

	d.lkgMu.Lock()
	d.lkgCache[serviceName] = healthy
	d.lkgMu.Unlock()

	span.SetAttribute("resolved.endpoint", healthy[0].Endpoint())
	return healthy[0], nil
}

// ResolveWithLKG returns active healthy instances, or if the registry returns no healthy instances,
// returns the Last-Known-Good cached instances as a resilience measure.
func (d *Discovery) ResolveWithLKG(serviceName string) ([]*registry.ServiceInstance, bool, error) {
	instances, err := d.ResolveAll(serviceName)
	if err == nil {
		return instances, false, nil
	}

	d.lkgMu.RLock()
	lkg, exists := d.lkgCache[serviceName]
	d.lkgMu.RUnlock()

	if exists && len(lkg) > 0 {
		return lkg, true, nil
	}

	return nil, false, err
}

func (d *Discovery) ResolveAll(serviceName string) ([]*registry.ServiceInstance, error) {
	_, span := tracing.StartSpan(context.Background(), "discovery.resolve-all")
	defer span.End()
	span.SetAttribute("service.name", serviceName)

	healthy := d.registry.GetHealthy(serviceName)
	if len(healthy) == 0 {
		err := d.buildDiagnosticError(serviceName)
		span.SetAttribute("resolve.error", err.Error())
		return nil, err
	}

	d.lkgMu.Lock()
	d.lkgCache[serviceName] = healthy
	d.lkgMu.Unlock()

	span.SetAttribute("resolved.count", fmt.Sprintf("%d", len(healthy)))
	return healthy, nil
}

func (d *Discovery) ResolveEndpoint(serviceName string) (string, error) {
	inst, err := d.Resolve(serviceName)
	if err != nil {
		return "", err
	}
	return inst.Endpoint(), nil
}

func (d *Discovery) ListServices() map[string][]*registry.ServiceInstance {
	return d.registry.GetAllServices()
}

func (d *Discovery) buildDiagnosticError(serviceName string) error {
	all := d.registry.GetAll(serviceName)
	if len(all) == 0 {
		return fmt.Errorf("service %q not registered", serviceName)
	}

	var diagnostics []string
	for _, inst := range all {
		reason := inst.LastProbeErr
		if reason == "" {
			reason = inst.Status.String()
		}
		diagnostics = append(diagnostics,
			fmt.Sprintf("  %s/%s (%s:%d) — %s", inst.Name, inst.ID, inst.Host, inst.Port, reason))
	}

	return fmt.Errorf("all %d instances of %q are unavailable:\n%s",
		len(all), serviceName, strings.Join(diagnostics, "\n"))
}
