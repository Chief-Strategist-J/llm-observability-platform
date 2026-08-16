export interface RouteConfig {
  path: string;
  serviceUrl: string;
  methods: string[];
}

export interface RateLimitRule {
  path: string;
  maxRequests: number;
  windowSeconds: number;
}

export interface ReverseProxyPort {
  registerRoute(config: RouteConfig): Promise<void>;
  applyRateLimitRule(rule: RateLimitRule): Promise<void>;
  revokeRouteAccess(path: string): Promise<void>;
}
