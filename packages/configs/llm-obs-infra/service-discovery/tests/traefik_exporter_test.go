package tests

import (
	"os"
	"testing"

	"github.com/llm-observability/platform/packages/configs/llm-obs-infra/service-discovery/registry"
	traefikpkg "github.com/llm-observability/platform/packages/configs/llm-obs-infra/service-discovery/traefik"
	"gopkg.in/yaml.v3"
)

func TestExporterGeneratesValidYAML(t *testing.T) {
	tmpFile := t.TempDir() + "/discovery.yml"

	reg := newTestRegistry()
	reg.Register(&registry.ServiceInstance{
		Name:     "test-svc",
		Host:     "localhost",
		Port:     8080,
		Protocol: "http",
		Status:   registry.StatusHealthy,
		HealthCheck: registry.HealthCheckSpec{
			Protocol: "http",
			Path:     "/health",
		},
	})
	reg.Register(&registry.ServiceInstance{
		Name:     "another-svc",
		Host:     "localhost",
		Port:     9090,
		Protocol: "http",
		Status:   registry.StatusHealthy,
		HealthCheck: registry.HealthCheckSpec{
			Protocol: "http",
			Path:     "/ping",
		},
	})

	config := traefikpkg.ExporterConfig{
		OutputPath:         tmpFile,
		DefaultDomain:      "llmobs.local",
		DefaultEntryPoints: []string{"websecure"},
		DefaultMiddlewares: []string{"security-headers@file"},
	}

	exporter := traefikpkg.NewExporter(reg, config)
	exporter.Export()

	data, err := os.ReadFile(tmpFile)
	if err != nil {
		t.Fatalf("failed to read generated file: %v", err)
	}

	var result map[string]interface{}
	if err := yaml.Unmarshal(data, &result); err != nil {
		t.Fatalf("generated invalid YAML: %v", err)
	}

	httpSection, ok := result["http"].(map[string]interface{})
	if !ok {
		t.Fatal("missing http section in generated YAML")
	}

	if _, ok := httpSection["routers"]; !ok {
		t.Fatal("missing routers in generated YAML")
	}
	if _, ok := httpSection["services"]; !ok {
		t.Fatal("missing services in generated YAML")
	}
}

func TestExporterExcludesUnhealthyInstances(t *testing.T) {
	tmpFile := t.TempDir() + "/discovery.yml"

	reg := newTestRegistry()
	inst := reg.Register(&registry.ServiceInstance{
		Name:     "unhealthy-export-svc",
		Host:     "localhost",
		Port:     8080,
		Protocol: "http",
		HealthCheck: registry.HealthCheckSpec{
			Protocol: "http",
			Path:     "/health",
		},
	})

	reg.UpdateStatus("unhealthy-export-svc", inst.ID, registry.StatusUnhealthy, "probe failed")

	config := traefikpkg.ExporterConfig{
		OutputPath:         tmpFile,
		DefaultDomain:      "llmobs.local",
		DefaultEntryPoints: []string{"websecure"},
		DefaultMiddlewares: []string{"security-headers@file"},
	}

	exporter := traefikpkg.NewExporter(reg, config)
	exporter.Export()

	data, err := os.ReadFile(tmpFile)
	if err != nil {
		t.Fatalf("failed to read generated file: %v", err)
	}

	var result map[string]interface{}
	yaml.Unmarshal(data, &result)

	httpSection := result["http"].(map[string]interface{})
	services, ok := httpSection["services"].(map[string]interface{})
	if ok {
		if _, exists := services["unhealthy-export-svc-discovery-svc"]; exists {
			t.Fatal("unhealthy instance should not be in exported config")
		}
	}
}
