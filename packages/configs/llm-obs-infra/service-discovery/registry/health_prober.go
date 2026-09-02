package registry

import (
	"context"
	"fmt"
	"log"
	"net"
	"net/http"
	"sync"
	"time"
)

type ProbeStrategy func(host string, port int, spec HealthCheckSpec) error

var probeStrategies = map[string]ProbeStrategy{
	"http": probeHTTP,
	"tcp":  probeTCP,
}

func RegisterProbeStrategy(protocol string, strategy ProbeStrategy) {
	probeStrategies[protocol] = strategy
}

func probeHTTP(host string, port int, spec HealthCheckSpec) error {
	url := fmt.Sprintf("http://%s:%d%s", host, port, spec.Path)
	client := &http.Client{Timeout: spec.Timeout}
	resp, err := client.Get(url)
	if err != nil {
		return fmt.Errorf("HTTP probe failed: %w", err)
	}
	defer resp.Body.Close()
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return fmt.Errorf("HTTP probe returned %d", resp.StatusCode)
	}
	return nil
}

func probeTCP(host string, port int, spec HealthCheckSpec) error {
	addr := fmt.Sprintf("%s:%d", host, port)
	conn, err := net.DialTimeout("tcp", addr, spec.Timeout)
	if err != nil {
		return fmt.Errorf("TCP probe failed: %w", err)
	}
	conn.Close()
	return nil
}

type HealthProberConfig struct {
	ProbeInterval time.Duration `json:"probeInterval"`
	MaxConcurrent int           `json:"maxConcurrent"`
}

var DefaultHealthProberConfig = HealthProberConfig{
	ProbeInterval: 5 * time.Second,
	MaxConcurrent: 10,
}

type HealthProber struct {
	registry *Registry
	config   HealthProberConfig
}

func NewHealthProber(registry *Registry, config HealthProberConfig) *HealthProber {
	return &HealthProber{registry: registry, config: config}
}

func (hp *HealthProber) Start(ctx context.Context) {
	ticker := time.NewTicker(hp.config.ProbeInterval)
	defer ticker.Stop()

	log.Printf("[health-prober] started (interval=%s, maxConcurrent=%d)",
		hp.config.ProbeInterval, hp.config.MaxConcurrent)

	for {
		select {
		case <-ctx.Done():
			log.Println("[health-prober] shutting down")
			return
		case <-ticker.C:
			hp.probeAll(ctx)
		}
	}
}

func (hp *HealthProber) probeAll(ctx context.Context) {
	snapshot := hp.registry.Snapshot()
	if len(snapshot) == 0 {
		return
	}

	sem := make(chan struct{}, hp.config.MaxConcurrent)
	var wg sync.WaitGroup

	for _, inst := range snapshot {
		if inst.Status == StatusDead {
			continue
		}

		wg.Add(1)
		sem <- struct{}{}

		go func(instance *ServiceInstance) {
			defer wg.Done()
			defer func() { <-sem }()

			hp.probeInstance(instance)
		}(inst)
	}

	wg.Wait()
}

func (hp *HealthProber) probeInstance(inst *ServiceInstance) {
	strategy, ok := probeStrategies[inst.HealthCheck.Protocol]
	if !ok {
		hp.registry.UpdateStatus(inst.Name, inst.ID, StatusUnhealthy,
			fmt.Sprintf("unsupported probe protocol: %s", inst.HealthCheck.Protocol))
		return
	}

	err := strategy(inst.Host, inst.Port, inst.HealthCheck)
	if err != nil {
		hp.registry.UpdateStatus(inst.Name, inst.ID, StatusUnhealthy, err.Error())
		return
	}

	if inst.Status != StatusHealthy {
		hp.registry.UpdateStatus(inst.Name, inst.ID, StatusHealthy, "")
	}
}
