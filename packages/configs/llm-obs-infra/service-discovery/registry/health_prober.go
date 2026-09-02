package registry

import (
	"context"
	"fmt"
	"log"
	"net"
	"net/http"
	"os/exec"
	"sync"
	"time"

	"github.com/llm-observability/platform/packages/configs/llm-obs-infra/service-discovery/tracing"
)

type ProbeStrategy func(ctx context.Context, host string, port int, spec HealthCheckSpec) error

var (
	probeStrategiesMu sync.RWMutex
	probeStrategies   = map[string]ProbeStrategy{
		"http": probeHTTP,
		"tcp":  probeTCP,
		"exec": probeExec,
	}
)

func RegisterProbeStrategy(protocol string, strategy ProbeStrategy) {
	probeStrategiesMu.Lock()
	defer probeStrategiesMu.Unlock()
	probeStrategies[protocol] = strategy
}

func getProbeStrategy(protocol string) (ProbeStrategy, bool) {
	probeStrategiesMu.RLock()
	defer probeStrategiesMu.RUnlock()
	strategy, ok := probeStrategies[protocol]
	return strategy, ok
}

func probeHTTP(ctx context.Context, host string, port int, spec HealthCheckSpec) error {
	url := fmt.Sprintf("http://%s:%d%s", host, port, spec.Path)
	client := &http.Client{Timeout: spec.Timeout}
	req, err := http.NewRequestWithContext(ctx, http.MethodGet, url, nil)
	if err != nil {
		return fmt.Errorf("HTTP request creation failed: %w", err)
	}

	tracing.InjectHTTPHeaders(ctx, req)

	resp, err := client.Do(req)
	if err != nil {
		return fmt.Errorf("HTTP probe failed: %w", err)
	}
	defer resp.Body.Close()
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return fmt.Errorf("HTTP probe returned %d", resp.StatusCode)
	}
	return nil
}

func probeTCP(ctx context.Context, host string, port int, spec HealthCheckSpec) error {
	addr := fmt.Sprintf("%s:%d", host, port)
	dialer := net.Dialer{Timeout: spec.Timeout}
	conn, err := dialer.DialContext(ctx, "tcp", addr)
	if err != nil {
		return fmt.Errorf("TCP probe failed: %w", err)
	}
	conn.Close()
	return nil
}

func probeExec(ctx context.Context, host string, port int, spec HealthCheckSpec) error {
	var cmd *exec.Cmd
	if len(spec.Command) > 0 {
		cmd = exec.CommandContext(ctx, spec.Command[0], spec.Command[1:]...)
	} else if spec.Path != "" {
		cmd = exec.CommandContext(ctx, "/bin/sh", "-c", spec.Path)
	} else {
		return fmt.Errorf("exec probe requires command slice or shell path spec")
	}

	output, err := cmd.CombinedOutput()
	if err != nil {
		return fmt.Errorf("exec probe failed (%v): %s", err, string(output))
	}
	return nil
}

type HealthProber struct {
	registry *Registry
	config   HealthProberConfig
}

func NewHealthProber(registry *Registry, config HealthProberConfig) *HealthProber {
	if config.DefaultSuccessTh <= 0 {
		config.DefaultSuccessTh = 2
	}
	if config.DefaultFailureTh <= 0 {
		config.DefaultFailureTh = 3
	}
	if config.MaxConcurrent <= 0 {
		config.MaxConcurrent = 10
	}
	return &HealthProber{registry: registry, config: config}
}

func (hp *HealthProber) Start(ctx context.Context) {
	ticker := time.NewTicker(hp.config.ProbeInterval)
	defer ticker.Stop()

	log.Printf("[health-prober] started (interval=%s, maxConcurrent=%d, successTh=%d, failTh=%d)",
		hp.config.ProbeInterval, hp.config.MaxConcurrent, hp.config.DefaultSuccessTh, hp.config.DefaultFailureTh)

	for {
		select {
		case <-ctx.Done():
			log.Println("[health-prober] shutting down")
			return
		case <-ticker.C:
			hp.probeAllConcurrent(ctx)
		}
	}
}

type probeJob struct {
	instance *ServiceInstance
}

type probeResult struct {
	instance *ServiceInstance
	err      error
}

func (hp *HealthProber) probeAllConcurrent(ctx context.Context) {
	snapshot := hp.registry.Snapshot()
	if len(snapshot) == 0 {
		return
	}

	var activeInstances []*ServiceInstance
	for _, inst := range snapshot {
		if inst.Status != StatusDead {
			activeInstances = append(activeInstances, inst)
		}
	}
	if len(activeInstances) == 0 {
		return
	}

	jobs := make(chan probeJob, len(activeInstances))
	results := make(chan probeResult, len(activeInstances))

	numWorkers := hp.config.MaxConcurrent
	if len(activeInstances) < numWorkers {
		numWorkers = len(activeInstances)
	}

	var wg sync.WaitGroup
	for w := 0; w < numWorkers; w++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			for job := range jobs {
				err := hp.executeProbe(ctx, job.instance)
				results <- probeResult{instance: job.instance, err: err}
			}
		}()
	}

	for _, inst := range activeInstances {
		jobs <- probeJob{instance: inst}
	}
	close(jobs)

	wg.Wait()
	close(results)

	for res := range results {
		hp.processResult(res.instance, res.err)
	}
}

func (hp *HealthProber) executeProbe(ctx context.Context, inst *ServiceInstance) error {
	strategy, ok := getProbeStrategy(inst.HealthCheck.Protocol)
	if !ok {
		return fmt.Errorf("unsupported probe protocol: %s", inst.HealthCheck.Protocol)
	}

	timeout := inst.HealthCheck.Timeout
	if timeout <= 0 {
		timeout = 2 * time.Second
	}
	probeCtx, cancel := context.WithTimeout(ctx, timeout)
	defer cancel()

	spanCtx, span := tracing.StartSpan(probeCtx, fmt.Sprintf("health-probe %s", inst.Name))
	defer span.End()
	span.SetAttribute("service.name", inst.Name)
	span.SetAttribute("instance.id", inst.ID)
	span.SetAttribute("probe.protocol", inst.HealthCheck.Protocol)
	span.SetAttribute("probe.host", inst.Host)
	span.SetAttribute("probe.port", fmt.Sprintf("%d", inst.Port))

	err := strategy(spanCtx, inst.Host, inst.Port, inst.HealthCheck)
	if err != nil {
		span.SetAttribute("probe.error", err.Error())
	} else {
		span.SetAttribute("probe.status", "ok")
	}
	return err
}

func (hp *HealthProber) processResult(inst *ServiceInstance, probeErr error) {
	failThreshold := inst.HealthCheck.FailureThreshold
	if failThreshold <= 0 {
		failThreshold = hp.config.DefaultFailureTh
	}
	successThreshold := inst.HealthCheck.SuccessThreshold
	if successThreshold <= 0 {
		successThreshold = hp.config.DefaultSuccessTh
	}

	if probeErr != nil {
		inst.ConsecutiveFails++
		inst.ConsecutiveSuccesses = 0

		if inst.ConsecutiveFails >= failThreshold {
			hp.registry.UpdateStatus(inst.Name, inst.ID, StatusUnhealthy, probeErr.Error())
		} else {
			log.Printf("[health-prober] probe failed for %s/%s (%d/%d): %v",
				inst.Name, inst.ID, inst.ConsecutiveFails, failThreshold, probeErr)
		}
		return
	}

	inst.ConsecutiveSuccesses++
	inst.ConsecutiveFails = 0

	if inst.Status == StatusUnhealthy || inst.Status == StatusDegraded {
		if inst.ConsecutiveSuccesses >= successThreshold {
			hp.registry.UpdateStatus(inst.Name, inst.ID, StatusHealthy, "")
		} else {
			log.Printf("[health-prober] probe passed for %s/%s (%d/%d required for recovery)",
				inst.Name, inst.ID, inst.ConsecutiveSuccesses, successThreshold)
		}
	} else if inst.Status != StatusHealthy {
		hp.registry.UpdateStatus(inst.Name, inst.ID, StatusHealthy, "")
	}
}
