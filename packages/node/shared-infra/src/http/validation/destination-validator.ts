import { resolveRules, type Rule } from "../../rules-engine";
import { RULES_ENGINE_CONSTANTS } from "../../rules-engine/constants";
import { errorRegistry } from "../../rules-engine/error-registry";

const BLOCKED_IP_REGEX = /^(127\.|169\.254\.|10\.|172\.(1[6-9]|2[0-9]|3[0-1])\.|192\.168\.|::1|0\.0\.0\.0)/;

async function resolveDnsAddresses(hostname: string): Promise<{ address: string }[]> {
  try {
    if (typeof window === "undefined") {
      const dns = await import(/* webpackIgnore: true */ "dns");
      return await dns.promises.lookup(hostname, { all: true });
    }
  } catch (err: any) {
    const errDesc = errorRegistry.get(RULES_ENGINE_CONSTANTS.ERR_SSRF_DNS_RESOLVED_BLOCKED);
    throw new Error(`${errDesc.message}: '${hostname}' - ${err?.message || String(err)}`);
  }
  return [];
}

export async function validateDestinationUrl(urlStr: string, allowedHosts?: string[]): Promise<URL> {
  let parsedUrl: URL;
  try {
    parsedUrl = new URL(urlStr);
  } catch {
    const errDesc = errorRegistry.get(RULES_ENGINE_CONSTANTS.ERR_SSRF_INVALID_URL);
    throw new Error(`${errDesc.message}: ${urlStr}`);
  }

  const destinationRules: Rule[] = [
    {
      id: RULES_ENGINE_CONSTANTS.ERR_SSRF_PROTOCOL_BLOCKED,
      name: "Enforce Secure Protocols (HTTP/HTTPS)",
      priority: 100,
      effect: "deny",
      conditions: [],
      asyncCheck: async (ctx) => {
        const protocol = ctx.protocol as string;
        return protocol !== "http:" && protocol !== "https:";
      },
    },
    {
      id: RULES_ENGINE_CONSTANTS.ERR_SSRF_IP_BLOCKED,
      name: "Block Restricted Private Subnets & Loopback",
      priority: 90,
      effect: "deny",
      conditions: [],
      asyncCheck: async (ctx) => {
        const hostname = ctx.hostname as string;
        const allowLoopback = ctx.allowLoopback || process.env.ALLOW_LOOPBACK_SSRF === "true" || process.env.NODE_ENV !== "production";
        if (allowLoopback) {
          return false;
        }
        return BLOCKED_IP_REGEX.test(hostname);
      },
    },
    {
      id: RULES_ENGINE_CONSTANTS.ERR_SSRF_ALLOWLIST_VIOLATION,
      name: "Enforce Destination Host Allowlist",
      priority: 80,
      effect: "deny",
      conditions: [],
      asyncCheck: async (ctx) => {
        const hosts = ctx.allowedHosts as string[] | undefined;
        const hostname = ctx.hostname as string;
        if (!hosts || hosts.length === 0) return false;
        return !hosts.includes(hostname);
      },
    },
    {
      id: RULES_ENGINE_CONSTANTS.ERR_SSRF_DNS_RESOLVED_BLOCKED,
      name: "Enforce DNS Resolved Subnet Check",
      priority: 70,
      effect: "deny",
      conditions: [],
      asyncCheck: async (ctx) => {
        const hostname = ctx.hostname as string;
        const allowLoopback = ctx.allowLoopback || process.env.ALLOW_LOOPBACK_SSRF === "true" || process.env.NODE_ENV !== "production";
        if (allowLoopback) {
          return false;
        }
        try {
          const addresses = await resolveDnsAddresses(hostname);
          for (const addr of addresses) {
            if (BLOCKED_IP_REGEX.test(addr.address)) {
              const errDesc = errorRegistry.get(RULES_ENGINE_CONSTANTS.ERR_SSRF_DNS_RESOLVED_BLOCKED);
              ctx.resolvedIpError = `${errDesc.message}: (${addr.address} for ${hostname})`;
              return true;
            }
          }
          return false;
        } catch (dnsErr: any) {
          if (dnsErr?.message?.includes("SSRF")) {
            ctx.resolvedIpError = dnsErr.message;
            return true;
          }
          const errDesc = errorRegistry.get(RULES_ENGINE_CONSTANTS.ERR_SSRF_DNS_RESOLVED_BLOCKED);
          ctx.resolvedIpError = `${errDesc.message}: '${hostname}' - ${dnsErr?.message || String(dnsErr)}`;
          return false;
        }
      },
    },
  ];

  const evalContext: Record<string, unknown> = {
    urlStr,
    hostname: parsedUrl.hostname,
    protocol: parsedUrl.protocol,
    allowedHosts,
  };

  const triggeredRules = await resolveRules(destinationRules, evalContext);

  if (triggeredRules.length > 0) {
    const primaryRule = triggeredRules[0];
    const errDesc = errorRegistry.get(primaryRule?.id || RULES_ENGINE_CONSTANTS.ERR_RULE_DENIED);
    const customMsg = evalContext.resolvedIpError as string | undefined;
    throw new Error(customMsg || `${errDesc.message}: ${parsedUrl.hostname}`);
  }

  return parsedUrl;
}
