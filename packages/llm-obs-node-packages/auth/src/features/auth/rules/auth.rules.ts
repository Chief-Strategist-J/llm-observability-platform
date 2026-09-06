export interface AuthRule {
  id: string;
  category: 'authentication' | 'authorization' | 'api_key';
  priority: number;
  effect: 'allow' | 'deny';
  condition: (ctx: { role?: string; revoked?: boolean; active?: boolean }) => boolean;
}

export const AUTH_DECLARATIVE_RULES: AuthRule[] = [
  {
    id: 'RULE_DENY_REVOKED_API_KEY',
    category: 'api_key',
    priority: 100,
    effect: 'deny',
    condition: (ctx) => ctx.revoked === true,
  },
  {
    id: 'RULE_ALLOW_ADMIN_ROLE',
    category: 'authorization',
    priority: 90,
    effect: 'allow',
    condition: (ctx) => ctx.role === 'admin',
  },
  {
    id: 'RULE_ALLOW_ACTIVE_USER',
    category: 'authentication',
    priority: 50,
    effect: 'allow',
    condition: (ctx) => ctx.active !== false,
  },
];

export function evaluateAuthRules(
  rules: AuthRule[],
  ctx: { role?: string; revoked?: boolean; active?: boolean }
): { allowed: boolean; matchedRuleId: string } {
  const sorted = [...rules].sort((a, b) => b.priority - a.priority);
  for (const rule of sorted) {
    if (rule.condition(ctx)) {
      return {
        allowed: rule.effect === 'allow',
        matchedRuleId: rule.id,
      };
    }
  }
  return { allowed: false, matchedRuleId: 'RULE_DEFAULT_DENY' };
}
