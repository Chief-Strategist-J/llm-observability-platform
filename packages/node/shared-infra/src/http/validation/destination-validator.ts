/**
 * @file destination-validator.ts
 * @description Rules-Engine Powered Destination & SSRF URL Validator.
 * 
 * ALGORITHM & RULE SPECIFICATION:
 * 1. Declarative SSRF Rule Evaluation:
 *    - Uses `resolveRules()` from `@core/rules-engine` to evaluate destination checks.
 *    - Rule 1 (`rule-ssrf-protocol-check`): Deny if protocol is not `http:` or `https:`.
 *    - Rule 2 (`rule-ssrf-blocked-ip`): Deny if hostname matches restricted private IP regex.
 *    - Rule 3 (`rule-ssrf-allowlist-check`): Deny if `allowedHosts` is present and hostname is missing from set.
 *    - Rule 4 (`rule-ssrf-dns-resolution`): Async check performing DNS lookup to detect TOCTOU / SSRF DNS rebinding to internal subnets.
 * 2. Strict Denial Execution:
 *    - Throws structured SSRF/Security exception if any `deny` rule triggers during rule resolution.
 */

import dns from "dns";
import { resolveRules, type Rule } from "../../rules-engine";

const BLOCKED_IP_REGEX = /^(127\.|169\.254\.|10\.|172\.(1[6-9]|2[0-9]|3[0-1])\.|192\.168\.|::1|0\.0\.0\.0)/;

export async function validateDestinationUrl(urlStr: string, allowedHosts?: string[]): Promise<URL> {
  let parsedUrl: URL;
  try {
    parsedUrl = new URL(urlStr);
  } catch {
    throw new Error(`Invalid URL: ${urlStr}`);
  }

  const destinationRules: Rule[] = [
    {
      id: "rule-ssrf-protocol-check",
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
      id: "rule-ssrf-blocked-ip",
      name: "Block Restricted Private Subnets & Loopback",
      priority: 90,
      effect: "deny",
      conditions: [],
      asyncCheck: async (ctx) => {
        const hostname = ctx.hostname as string;
        return BLOCKED_IP_REGEX.test(hostname);
      },
    },
    {
      id: "rule-ssrf-allowlist-check",
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
      id: "rule-ssrf-dns-resolution",
      name: "Enforce DNS Resolved Subnet Check",
      priority: 70,
      effect: "deny",
      conditions: [],
      asyncCheck: async (ctx) => {
        const hostname = ctx.hostname as string;
        try {
          const addresses = await dns.promises.lookup(hostname, { all: true });
          for (const addr of addresses) {
            if (BLOCKED_IP_REGEX.test(addr.address)) {
              ctx.resolvedIpError = `SSRF Blocked: Resolved IP ${addr.address} for host ${hostname} is a restricted private IP`;
              return true; // Trigger deny rule
            }
          }
          return false;
        } catch (dnsErr: any) {
          if (dnsErr?.message?.includes("SSRF Blocked")) {
            ctx.resolvedIpError = dnsErr.message;
            return true;
          }
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
    if (primaryRule?.id === "rule-ssrf-protocol-check") {
      throw new Error(`Blocked insecure URL protocol scheme: ${parsedUrl.protocol}`);
    }
    if (primaryRule?.id === "rule-ssrf-blocked-ip") {
      throw new Error(`SSRF Blocked: Destination IP/Host ${parsedUrl.hostname} is a restricted private/internal address`);
    }
    if (primaryRule?.id === "rule-ssrf-allowlist-check") {
      throw new Error(`SSRF Violation: Target host ${parsedUrl.hostname} is not in destination allowlist`);
    }
    if (primaryRule?.id === "rule-ssrf-dns-resolution") {
      const customMsg = evalContext.resolvedIpError as string | undefined;
      throw new Error(customMsg || `SSRF Blocked: Resolved IP for host ${parsedUrl.hostname} is restricted`);
    }
    throw new Error(`SSRF Violation: Target URL failed security validation rule ${primaryRule?.name || "Unknown"}`);
  }


  return parsedUrl;
}
