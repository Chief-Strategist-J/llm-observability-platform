package loadbalancer

import (
	"fmt"
	"hash/fnv"
	"math/rand"
	"sort"
	"sync"
	"sync/atomic"

	"github.com/llm-observability/platform/packages/configs/llm-obs-infra/service-discovery/registry"
)

type Algorithm string

const (
	AlgorithmRoundRobin      Algorithm = "round_robin"
	AlgorithmWeightedRR      Algorithm = "weighted_round_robin"
	AlgorithmLeastConn       Algorithm = "least_connections"
	AlgorithmP2C             Algorithm = "power_of_two_choices"
	AlgorithmConsistentHash  Algorithm = "consistent_hash"
)

type Balancer interface {
	Pick(instances []*registry.ServiceInstance, key string) (*registry.ServiceInstance, error)
}

type BalancerFactory func() Balancer

var balancerFactories = map[Algorithm]BalancerFactory{
	AlgorithmRoundRobin:     func() Balancer { return &RoundRobin{} },
	AlgorithmWeightedRR:     func() Balancer { return &WeightedRoundRobin{} },
	AlgorithmLeastConn:      func() Balancer { return NewLeastConnections() },
	AlgorithmP2C:            func() Balancer { return &PowerOfTwoChoices{} },
	AlgorithmConsistentHash: func() Balancer { return NewConsistentHash(150) },
}

func RegisterAlgorithm(name Algorithm, factory BalancerFactory) {
	balancerFactories[name] = factory
}

func NewBalancer(algorithm Algorithm) (Balancer, error) {
	factory, ok := balancerFactories[algorithm]
	if !ok {
		return nil, fmt.Errorf("unknown load balancer algorithm: %s", algorithm)
	}
	return factory(), nil
}

type RoundRobin struct {
	counter atomic.Uint64
}

func (rr *RoundRobin) Pick(instances []*registry.ServiceInstance, _ string) (*registry.ServiceInstance, error) {
	if len(instances) == 0 {
		return nil, fmt.Errorf("no instances available")
	}
	idx := rr.counter.Add(1) % uint64(len(instances))
	return instances[idx], nil
}

type WeightedRoundRobin struct {
	mu             sync.Mutex
	currentWeights map[string]int
}

func (wrr *WeightedRoundRobin) Pick(instances []*registry.ServiceInstance, _ string) (*registry.ServiceInstance, error) {
	if len(instances) == 0 {
		return nil, fmt.Errorf("no instances available")
	}

	wrr.mu.Lock()
	defer wrr.mu.Unlock()

	if wrr.currentWeights == nil {
		wrr.currentWeights = make(map[string]int)
	}

	totalWeight := 0
	for _, inst := range instances {
		totalWeight += inst.Weight
	}

	var best *registry.ServiceInstance
	bestWeight := -1

	for _, inst := range instances {
		wrr.currentWeights[inst.ID] += inst.Weight
		if wrr.currentWeights[inst.ID] > bestWeight {
			bestWeight = wrr.currentWeights[inst.ID]
			best = inst
		}
	}

	if best != nil {
		wrr.currentWeights[best.ID] -= totalWeight
	}

	return best, nil
}

type LeastConnections struct {
	inflight sync.Map
}

func NewLeastConnections() *LeastConnections {
	return &LeastConnections{}
}

func (lc *LeastConnections) Pick(instances []*registry.ServiceInstance, _ string) (*registry.ServiceInstance, error) {
	if len(instances) == 0 {
		return nil, fmt.Errorf("no instances available")
	}

	var best *registry.ServiceInstance
	var bestCount int64 = -1

	for _, inst := range instances {
		val, _ := lc.inflight.LoadOrStore(inst.ID, new(atomic.Int64))
		count := val.(*atomic.Int64).Load()
		if bestCount == -1 || count < bestCount {
			bestCount = count
			best = inst
		}
	}

	if best != nil {
		val, _ := lc.inflight.LoadOrStore(best.ID, new(atomic.Int64))
		val.(*atomic.Int64).Add(1)
	}

	return best, nil
}

func (lc *LeastConnections) Release(instanceID string) {
	val, ok := lc.inflight.Load(instanceID)
	if ok {
		val.(*atomic.Int64).Add(-1)
	}
}

type PowerOfTwoChoices struct{}

func (p2c *PowerOfTwoChoices) Pick(instances []*registry.ServiceInstance, _ string) (*registry.ServiceInstance, error) {
	if len(instances) == 0 {
		return nil, fmt.Errorf("no instances available")
	}
	if len(instances) == 1 {
		return instances[0], nil
	}

	a := rand.Intn(len(instances))
	b := rand.Intn(len(instances))
	for b == a {
		b = rand.Intn(len(instances))
	}

	if instances[a].Weight >= instances[b].Weight {
		return instances[a], nil
	}
	return instances[b], nil
}

type hashRingNode struct {
	hash       uint32
	instanceID string
}

type ConsistentHash struct {
	mu           sync.RWMutex
	ring         []hashRingNode
	virtualNodes int
	instanceMap  map[string]*registry.ServiceInstance
}

func NewConsistentHash(virtualNodes int) *ConsistentHash {
	return &ConsistentHash{
		virtualNodes: virtualNodes,
		instanceMap:  make(map[string]*registry.ServiceInstance),
	}
}

func (ch *ConsistentHash) Pick(instances []*registry.ServiceInstance, key string) (*registry.ServiceInstance, error) {
	if len(instances) == 0 {
		return nil, fmt.Errorf("no instances available")
	}
	if key == "" {
		return instances[rand.Intn(len(instances))], nil
	}

	ch.rebuild(instances)

	ch.mu.RLock()
	defer ch.mu.RUnlock()

	hash := fnvHash(key)
	idx := sort.Search(len(ch.ring), func(i int) bool {
		return ch.ring[i].hash >= hash
	})
	if idx >= len(ch.ring) {
		idx = 0
	}

	inst, ok := ch.instanceMap[ch.ring[idx].instanceID]
	if !ok {
		return instances[0], nil
	}
	return inst, nil
}

func (ch *ConsistentHash) rebuild(instances []*registry.ServiceInstance) {
	ch.mu.Lock()
	defer ch.mu.Unlock()

	ch.ring = ch.ring[:0]
	ch.instanceMap = make(map[string]*registry.ServiceInstance, len(instances))

	for _, inst := range instances {
		ch.instanceMap[inst.ID] = inst
		for i := 0; i < ch.virtualNodes; i++ {
			vKey := fmt.Sprintf("%s-%d", inst.ID, i)
			ch.ring = append(ch.ring, hashRingNode{
				hash:       fnvHash(vKey),
				instanceID: inst.ID,
			})
		}
	}

	sort.Slice(ch.ring, func(i, j int) bool {
		return ch.ring[i].hash < ch.ring[j].hash
	})
}

func fnvHash(key string) uint32 {
	h := fnv.New32a()
	h.Write([]byte(key))
	return h.Sum32()
}
