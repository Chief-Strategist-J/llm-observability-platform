import type { ReverseProxyPort, RouteConfig, RateLimitRule } from './proxy.interface';

export class EnvoyProxyAdapter implements ReverseProxyPort {
  private readonly envoyClusters = new Map<string, RouteConfig>();
  private readonly envoyRateFilters = new Map<string, RateLimitRule>();

  async registerRoute(config: RouteConfig): Promise<void> {
    this.envoyClusters.set(config.path, config);
  }

  async applyRateLimitRule(rule: RateLimitRule): Promise<void> {
    this.envoyRateFilters.set(rule.path, rule);
  }

  async revokeRouteAccess(path: string): Promise<void> {
    this.envoyClusters.delete(path);
    this.envoyRateFilters.delete(path);
  }
}
