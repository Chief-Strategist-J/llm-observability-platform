import type { ReverseProxyPort, RouteConfig, RateLimitRule } from './proxy.interface';

export class TraefikProxyAdapter implements ReverseProxyPort {
  private readonly routes = new Map<string, RouteConfig>();
  private readonly rateLimits = new Map<string, RateLimitRule>();

  async registerRoute(config: RouteConfig): Promise<void> {
    this.routes.set(config.path, config);
  }

  async applyRateLimitRule(rule: RateLimitRule): Promise<void> {
    this.rateLimits.set(rule.path, rule);
  }

  async revokeRouteAccess(path: string): Promise<void> {
    this.routes.delete(path);
    this.rateLimits.delete(path);
  }
}
