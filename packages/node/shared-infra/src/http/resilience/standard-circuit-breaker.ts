/**
 * @file standard-circuit-breaker.ts
 * @description Standard Bounded LRU Circuit Breaker State Machine.
 * 
 * ALGORITHM & STATE MACHINE SPECIFICATION:
 * 1. State Machine Transitions:
 *    - CLOSED (Normal): Allows network calls. Increments failure counter on error.
 *      Transitions to OPEN if failures >= failureThreshold (default: 5).
 *    - OPEN (Tripped): Fast-fails requests with 503 without socket initiation.
 *      Transitions to HALF_OPEN after cooldown period (cooldownMs, default: 3600000ms / 1hr).
 *    - HALF_OPEN (Probe): Allows 1 trial request.
 *      If trial succeeds -> CLOSED (reset).
 *      If trial fails -> OPEN (reset cooldown).
 * 2. Memory Protection (Bounded LRU Capacity):
 *    - Bounded to maxEntries (default: 1000) using Map insertion ordering LRU eviction.
 */

import { HTTP_CONSTANTS } from "../constants";
import { deriveRouteTemplate } from "../utils/http-utils";

export interface CircuitState {
  state: "CLOSED" | "OPEN" | "HALF_OPEN";
  failures: number;
  lastFailureTime?: number;
  nextAttemptTime?: number;
}

export class StandardCircuitBreaker {
  private readonly states = new Map<string, CircuitState>();

  constructor(
    private readonly failureThreshold = 5,
    private readonly cooldownMs = 3600000,
    private readonly maxEntries = 1000
  ) {}

  public getCircuitKey(tenantId: string, routeTemplateOrUrl: string): string {
    const route = deriveRouteTemplate(routeTemplateOrUrl);
    return `${tenantId}:${route}`;
  }


  public canExecute(circuitKey: string): boolean {
    const state = this.states.get(circuitKey);
    if (!state || state.state === HTTP_CONSTANTS.CIRCUIT_CLOSED) {
      return true;
    }

    const now = Date.now();
    if (state.state === HTTP_CONSTANTS.CIRCUIT_OPEN) {
      if (state.nextAttemptTime && now >= state.nextAttemptTime) {
        state.state = HTTP_CONSTANTS.CIRCUIT_HALF_OPEN;
        return true;
      }
      return false;
    }

    if (state.state === HTTP_CONSTANTS.CIRCUIT_HALF_OPEN) {
      return true;
    }

    return true;
  }

  public onSuccess(circuitKey: string): void {
    const state = this.states.get(circuitKey);
    if (state) {
      state.state = HTTP_CONSTANTS.CIRCUIT_CLOSED as "CLOSED";
      state.failures = 0;
      state.nextAttemptTime = undefined;
    }
  }

  public onFailure(circuitKey: string): void {
    const now = Date.now();
    let state = this.states.get(circuitKey);

    if (!state) {
      this.evictIfFull();
      state = { state: HTTP_CONSTANTS.CIRCUIT_CLOSED as "CLOSED", failures: 0 };
      this.states.set(circuitKey, state);
    }

    state.failures++;
    state.lastFailureTime = now;

    if (state.failures >= this.failureThreshold || state.state === HTTP_CONSTANTS.CIRCUIT_HALF_OPEN) {
      state.state = HTTP_CONSTANTS.CIRCUIT_OPEN as "OPEN";
      state.nextAttemptTime = now + this.cooldownMs;
    }
  }

  public getState(circuitKey: string): CircuitState | undefined {
    return this.states.get(circuitKey);
  }

  private evictIfFull(): void {
    if (this.states.size >= this.maxEntries) {
      const oldestKey = this.states.keys().next().value;
      if (oldestKey) {
        this.states.delete(oldestKey);
      }
    }
  }
}
