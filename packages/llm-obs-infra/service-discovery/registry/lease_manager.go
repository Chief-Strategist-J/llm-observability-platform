package registry

import (
	"context"
	"log"
	"time"
)

type LeaseManager struct {
	registry *Registry
	config   LeaseManagerConfig
}

func NewLeaseManager(registry *Registry, config LeaseManagerConfig) *LeaseManager {
	return &LeaseManager{registry: registry, config: config}
}

func (lm *LeaseManager) Start(ctx context.Context) {
	ticker := time.NewTicker(lm.config.SweepInterval)
	defer ticker.Stop()

	log.Printf("[lease-manager] started (sweep=%s, heartbeatTTL=%s, evictionTTL=%s)",
		lm.config.SweepInterval, lm.config.HeartbeatTTL, lm.config.EvictionTTL)

	for {
		select {
		case <-ctx.Done():
			log.Println("[lease-manager] shutting down")
			return
		case <-ticker.C:
			lm.sweep()
		}
	}
}

func (lm *LeaseManager) sweep() {
	now := time.Now()
	snapshot := lm.registry.Snapshot()

	for _, inst := range snapshot {
		elapsed := now.Sub(inst.LastHeartbeat)

		if elapsed > lm.config.EvictionTTL {
			lm.registry.EvictInstance(inst.Name, inst.ID)
		} else if elapsed > lm.config.HeartbeatTTL && inst.Status == StatusHealthy {
			lm.registry.UpdateStatus(inst.Name, inst.ID, StatusUnhealthy, "heartbeat expired")
		}
	}
}
