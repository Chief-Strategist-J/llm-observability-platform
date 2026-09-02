package registry

import (
	"crypto/rand"
	"encoding/hex"
	"fmt"
	"log"
	"sync"
	"time"
)

type Registry struct {
	mu         sync.RWMutex
	instances  map[string]map[string]*ServiceInstance
	listeners  []chan RegistryEvent
	listenerMu sync.RWMutex
	defaults   InstanceDefaults
}

type InstanceDefaults struct {
	Weight              int           `json:"weight"`
	HealthCheckInterval time.Duration `json:"healthCheckInterval"`
	HealthCheckTimeout  time.Duration `json:"healthCheckTimeout"`
}

var DefaultInstanceDefaults = InstanceDefaults{
	Weight:              100,
	HealthCheckInterval: 5 * time.Second,
	HealthCheckTimeout:  2 * time.Second,
}

func NewRegistry(defaults InstanceDefaults) *Registry {
	return &Registry{
		instances: make(map[string]map[string]*ServiceInstance),
		listeners: make([]chan RegistryEvent, 0),
		defaults:  defaults,
	}
}

func generateID() string {
	b := make([]byte, 8)
	_, _ = rand.Read(b)
	return hex.EncodeToString(b)
}

func (r *Registry) applyDefaults(inst *ServiceInstance) {
	if inst.ID == "" {
		inst.ID = generateID()
	}
	if inst.Weight <= 0 {
		inst.Weight = r.defaults.Weight
	}
	if inst.HealthCheck.Interval == 0 {
		inst.HealthCheck.Interval = r.defaults.HealthCheckInterval
	}
	if inst.HealthCheck.Timeout == 0 {
		inst.HealthCheck.Timeout = r.defaults.HealthCheckTimeout
	}
}

func (r *Registry) findInstanceLocked(serviceName, instanceID string) (*ServiceInstance, bool) {
	instances, ok := r.instances[serviceName]
	if !ok {
		return nil, false
	}
	inst, ok := instances[instanceID]
	return inst, ok
}

func (r *Registry) Register(instance *ServiceInstance) *ServiceInstance {
	r.mu.Lock()
	defer r.mu.Unlock()

	r.applyDefaults(instance)

	now := time.Now()
	instance.RegisteredAt = now
	instance.LastHeartbeat = now
	instance.Status = StatusHealthy

	if r.instances[instance.Name] == nil {
		r.instances[instance.Name] = make(map[string]*ServiceInstance)
	}
	r.instances[instance.Name][instance.ID] = instance

	log.Printf("[registry] registered %s/%s at %s:%d", instance.Name, instance.ID, instance.Host, instance.Port)
	r.emitAsync(RegistryEvent{Type: EventRegistered, Instance: instance, Time: now})

	return instance
}

func (r *Registry) Deregister(serviceName, instanceID string) error {
	r.mu.Lock()
	defer r.mu.Unlock()

	inst, ok := r.findInstanceLocked(serviceName, instanceID)
	if !ok {
		return fmt.Errorf("instance %q not found in service %q", instanceID, serviceName)
	}

	delete(r.instances[serviceName], instanceID)
	if len(r.instances[serviceName]) == 0 {
		delete(r.instances, serviceName)
	}

	log.Printf("[registry] deregistered %s/%s", serviceName, instanceID)
	r.emitAsync(RegistryEvent{Type: EventDeregistered, Instance: inst, Time: time.Now()})

	return nil
}

func (r *Registry) Heartbeat(serviceName, instanceID string) error {
	r.mu.Lock()
	defer r.mu.Unlock()

	inst, ok := r.findInstanceLocked(serviceName, instanceID)
	if !ok {
		return fmt.Errorf("instance %q not found in service %q", instanceID, serviceName)
	}

	inst.LastHeartbeat = time.Now()

	if inst.Status == StatusUnhealthy && inst.LastProbeErr == "heartbeat expired" {
		inst.Status = StatusHealthy
		inst.LastProbeErr = ""
		r.emitAsync(RegistryEvent{Type: EventStatusChanged, Instance: inst, Time: time.Now()})
	}

	return nil
}

func (r *Registry) UpdateStatus(serviceName, instanceID string, status HealthStatus, probeErr string) {
	r.mu.Lock()
	defer r.mu.Unlock()

	inst, ok := r.findInstanceLocked(serviceName, instanceID)
	if !ok {
		return
	}

	oldStatus := inst.Status
	inst.Status = status
	inst.LastProbeAt = time.Now()
	inst.LastProbeErr = probeErr

	if oldStatus != status {
		log.Printf("[registry] status changed %s/%s: %s -> %s (%s)", serviceName, instanceID, oldStatus, status, probeErr)
		r.emitAsync(RegistryEvent{Type: EventStatusChanged, Instance: inst, Time: time.Now()})
	}
}

func (r *Registry) GetAll(serviceName string) []*ServiceInstance {
	r.mu.RLock()
	defer r.mu.RUnlock()

	instances, ok := r.instances[serviceName]
	if !ok {
		return nil
	}

	result := make([]*ServiceInstance, 0, len(instances))
	for _, inst := range instances {
		result = append(result, inst)
	}
	return result
}

func (r *Registry) GetHealthy(serviceName string) []*ServiceInstance {
	r.mu.RLock()
	defer r.mu.RUnlock()

	instances, ok := r.instances[serviceName]
	if !ok {
		return nil
	}

	result := make([]*ServiceInstance, 0, len(instances))
	for _, inst := range instances {
		if inst.Status == StatusHealthy || inst.Status == StatusDegraded {
			result = append(result, inst)
		}
	}
	return result
}

func (r *Registry) GetAllServices() map[string][]*ServiceInstance {
	r.mu.RLock()
	defer r.mu.RUnlock()

	result := make(map[string][]*ServiceInstance, len(r.instances))
	for name, instances := range r.instances {
		list := make([]*ServiceInstance, 0, len(instances))
		for _, inst := range instances {
			list = append(list, inst)
		}
		result[name] = list
	}
	return result
}

func (r *Registry) GetInstance(serviceName, instanceID string) (*ServiceInstance, bool) {
	r.mu.RLock()
	defer r.mu.RUnlock()

	return r.findInstanceLocked(serviceName, instanceID)
}

func (r *Registry) Subscribe() chan RegistryEvent {
	ch := make(chan RegistryEvent, 128)
	r.listenerMu.Lock()
	r.listeners = append(r.listeners, ch)
	r.listenerMu.Unlock()
	return ch
}

func (r *Registry) Unsubscribe(ch chan RegistryEvent) {
	r.listenerMu.Lock()
	defer r.listenerMu.Unlock()

	for i, listener := range r.listeners {
		if listener == ch {
			r.listeners = append(r.listeners[:i], r.listeners[i+1:]...)
			close(ch)
			return
		}
	}
}

func (r *Registry) emitAsync(event RegistryEvent) {
	r.listenerMu.RLock()
	listeners := make([]chan RegistryEvent, len(r.listeners))
	copy(listeners, r.listeners)
	r.listenerMu.RUnlock()

	go func() {
		for _, ch := range listeners {
			select {
			case ch <- event:
			default:
			}
		}
	}()
}

func (r *Registry) EvictInstance(serviceName, instanceID string) {
	r.mu.Lock()
	inst, ok := r.findInstanceLocked(serviceName, instanceID)
	if !ok {
		r.mu.Unlock()
		return
	}

	inst.Status = StatusDead
	delete(r.instances[serviceName], instanceID)
	if len(r.instances[serviceName]) == 0 {
		delete(r.instances, serviceName)
	}
	r.mu.Unlock()

	log.Printf("[registry] evicted %s/%s", serviceName, instanceID)
	r.emitAsync(RegistryEvent{Type: EventHeartbeatExpired, Instance: inst, Time: time.Now()})
}

func (r *Registry) Snapshot() []*ServiceInstance {
	r.mu.RLock()
	defer r.mu.RUnlock()

	var all []*ServiceInstance
	for _, instances := range r.instances {
		for _, inst := range instances {
			all = append(all, inst)
		}
	}
	return all
}
