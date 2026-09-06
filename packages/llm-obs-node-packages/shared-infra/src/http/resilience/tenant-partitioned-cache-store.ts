/**
 * @file tenant-partitioned-cache-store.ts
 * @description Multi-Tenant Isolated Partitioned LRU Cache Store.
 * 
 * ALGORITHM & SPECIFICATION:
 * 1. Two-Level Partitioned Memory Map:
 *    - Structure: `Map<tenantId, Map<requestKey, CacheEntry>>`.
 *    - Guarantees zero cross-tenant data leaks.
 * 2. Invalidation Mechanics:
 *    - `clear(tenantId)`: Instantly invalidates all entries for the target tenant partition
 *      when mutating write RPCs (POST, PUT, PATCH, DELETE) occur.
 * 3. Bounded Partition LRU Capacity & TTL Eviction:
 *    - Each partition enforces `maxPartitionSize` (default: 100 entries) with Map LRU eviction.
 *    - Evicts items when `Date.now() >= expiresAt`.
 */

interface CacheEntry<T = unknown> {
  value: T;
  expiresAt: number;
}

export class TenantPartitionedCacheStore {
  private readonly partitions = new Map<string, Map<string, CacheEntry>>();

  constructor(private readonly maxPartitionSize = 100) {}

  public get<T>(tenantId: string, key: string): T | undefined {
    const partition = this.partitions.get(tenantId);
    if (!partition) return undefined;

    const entry = partition.get(key);
    if (!entry) return undefined;

    if (Date.now() >= entry.expiresAt) {
      partition.delete(key);
      return undefined;
    }

    return entry.value as T;
  }

  public set<T>(tenantId: string, key: string, value: T, ttlMs = 5000): void {
    let partition = this.partitions.get(tenantId);
    if (!partition) {
      partition = new Map<string, CacheEntry>();
      this.partitions.set(tenantId, partition);
    }

    if (partition.size >= this.maxPartitionSize) {
      const oldestKey = partition.keys().next().value;
      if (oldestKey) {
        partition.delete(oldestKey);
      }
    }

    partition.set(key, {
      value,
      expiresAt: Date.now() + ttlMs,
    });
  }

  public clear(tenantId: string): void {
    this.partitions.delete(tenantId);
  }

  public clearAll(): void {
    this.partitions.clear();
  }
}
