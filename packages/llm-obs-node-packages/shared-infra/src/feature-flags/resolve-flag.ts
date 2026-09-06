import type { Rule } from '../rules-engine/rule.types';
import { resolveRules } from '../rules-engine/evaluate';

export async function resolveFlag(
  flagName: string,
  ctx: Record<string, unknown>,
  flagRules: Rule[],
  rolloutPercentage?: number,
): Promise<boolean> {
  const matchingRules = flagRules.filter((r) => r.category === flagName || r.id === flagName);
  if (matchingRules.length > 0) {
    const activeRules = await resolveRules(matchingRules, ctx);
    const hasDeny = activeRules.some((r) => r.effect === 'deny');
    if (hasDeny) return false;

    const hasAllow = activeRules.some((r) => r.effect === 'allow');
    if (hasAllow) {
      if (rolloutPercentage !== undefined && rolloutPercentage < 100) {
        const userId = (ctx.userId ?? ctx.id ?? '') as string;
        let hash = 0;
        for (let i = 0; i < userId.length; i++) {
          hash = (hash << 5) - hash + userId.charCodeAt(i);
          hash |= 0;
        }
        const bucket = Math.abs(hash) % 100;
        return bucket < rolloutPercentage;
      }
      return true;
    }
  }

  if (rolloutPercentage !== undefined) {
    const userId = (ctx.userId ?? ctx.id ?? '') as string;
    let hash = 0;
    for (let i = 0; i < userId.length; i++) {
      hash = (hash << 5) - hash + userId.charCodeAt(i);
      hash |= 0;
    }
    const bucket = Math.abs(hash) % 100;
    return bucket < rolloutPercentage;
  }

  return false;
}
