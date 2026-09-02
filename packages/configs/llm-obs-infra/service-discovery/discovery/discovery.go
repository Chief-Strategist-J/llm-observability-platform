package discovery

import (
	"context"
	"fmt"
	"strings"

	"github.com/llm-observability/platform/packages/configs/llm-obs-infra/service-discovery/registry"
	"github.com/llm-observability/platform/packages/configs/llm-obs-infra/service-discovery/tracing"
)

type Discovery struct {
	registry *registry.Registry
}

func NewDiscovery(reg *registry.Registry) *Discovery {
	return &Discovery{registry: reg}
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
	span.SetAttribute("resolved.endpoint", healthy[0].Endpoint())
	return healthy[0], nil
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

func (d *Discovery) Watch(serviceName string) chan registry.RegistryEvent {
	allEvents := d.registry.Subscribe()
	filtered := make(chan registry.RegistryEvent, 64)

	go func() {
		defer close(filtered)
		for event := range allEvents {
			if event.Instance != nil && event.Instance.Name == serviceName {
				filtered <- event
			}
		}
	}()

	return filtered
}

func (d *Discovery) WatchAll() chan registry.RegistryEvent {
	return d.registry.Subscribe()
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
