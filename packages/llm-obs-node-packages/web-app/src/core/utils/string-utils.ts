import { errorRegistry, RULES_ENGINE_CONSTANTS } from "@observability/shared-infra";

export function normalizeString(input?: string | null): string {
  if (!input || typeof input !== "string") return "";
  return input
    .trim()
    .toLowerCase()
    .replace(/[\s\-_.]+/g, "_");
}

export function compareNormalized(strA?: string | null, strB?: string | null): boolean {
  return normalizeString(strA) === normalizeString(strB);
}

export function matchesAnyNormalized(
  target?: string | null,
  candidates: (string | number)[] = []
): boolean {
  const normTarget = normalizeString(target);
  if (!normTarget) return false;

  return candidates.some((cand) => {
    const normCand = normalizeString(String(cand));
    if (!normCand) return false;
    return normTarget === normCand || normTarget.includes(normCand) || normCand.includes(normTarget);
  });
}

export function isUnauthorizedError(err: any): boolean {
  if (!err) return false;

  if (err.status === 401 || err.statusCode === 401 || err.response?.status === 401) {
    return true;
  }

  const code = err.code || err.errorCode || err.name;
  const message = err.message || err.error || err.details;

  const UNAUTHORIZED_TOKENS = [
    "unauthorized",
    "token_expired",
    "expired",
    "invalid_token",
    "jwt_expired",
    "session_expired",
    "auth_failed",
    "permission_denied",
  ];

  return (
    matchesAnyNormalized(code, UNAUTHORIZED_TOKENS) ||
    matchesAnyNormalized(message, UNAUTHORIZED_TOKENS)
  );
}

export function formatUserFacingError(err: any, fallback?: string): string {
  if (!err) {
    return fallback || errorRegistry.get(RULES_ENGINE_CONSTANTS.ERR_UNKNOWN).message;
  }

  const status = typeof err === "object" ? Number(err.status || err.statusCode || err.response?.status) : NaN;
  if (status === 401) {
    return errorRegistry.get(RULES_ENGINE_CONSTANTS.ERR_UNAUTHORIZED).message;
  }
  if (status === 403) {
    return errorRegistry.get(RULES_ENGINE_CONSTANTS.ERR_FORBIDDEN).message;
  }
  if (status === 404) {
    return errorRegistry.get(RULES_ENGINE_CONSTANTS.ERR_NOT_FOUND).message;
  }
  if (status === 502 || status === 503) {
    return errorRegistry.get(RULES_ENGINE_CONSTANTS.ERR_SERVICE_UNREACHABLE).message;
  }
  if (status === 500) {
    return errorRegistry.get(RULES_ENGINE_CONSTANTS.ERR_HTTP_FAILED).message;
  }

  const code = String(err.code || err.errorCode || err.id || "").toUpperCase();
  if (
    code === RULES_ENGINE_CONSTANTS.ERR_CIRCUIT_OPEN ||
    code === RULES_ENGINE_CONSTANTS.ERR_SERVICE_UNREACHABLE ||
    code === "ECONNREFUSED" ||
    code === "ENOTFOUND" ||
    code === "FETCH_ERROR"
  ) {
    return errorRegistry.get(RULES_ENGINE_CONSTANTS.ERR_SERVICE_UNREACHABLE).message;
  }
  if (code === RULES_ENGINE_CONSTANTS.ERR_SSRF_PROTOCOL_BLOCKED || code === RULES_ENGINE_CONSTANTS.ERR_VALIDATION_FAILED) {
    return errorRegistry.get(RULES_ENGINE_CONSTANTS.ERR_VALIDATION_FAILED).message;
  }
  if (
    code === RULES_ENGINE_CONSTANTS.ERR_SSRF_IP_BLOCKED ||
    code === RULES_ENGINE_CONSTANTS.ERR_SSRF_ALLOWLIST_VIOLATION ||
    code === RULES_ENGINE_CONSTANTS.ERR_SSRF_DNS_RESOLVED_BLOCKED ||
    code === RULES_ENGINE_CONSTANTS.ERR_RULE_DENIED
  ) {
    return errorRegistry.get(RULES_ENGINE_CONSTANTS.ERR_RULE_DENIED).message;
  }

  if (code) {
    const descriptor = errorRegistry.get(code);
    if (descriptor && descriptor.code !== RULES_ENGINE_CONSTANTS.ERR_UNKNOWN) {
      return descriptor.message;
    }
  }

  const rawMsg = String(err.message || "");
  if (
    rawMsg.includes("Circuit breaker is OPEN") ||
    rawMsg.includes("CircuitBreaker") ||
    rawMsg.includes("blocked due to recent failures")
  ) {
    return errorRegistry.get(RULES_ENGINE_CONSTANTS.ERR_SERVICE_UNREACHABLE).message;
  }

  if (typeof err.message === "string" && err.message.trim().length > 0 && !err.message.includes("at ")) {
    return err.message;
  }

  return fallback || errorRegistry.get(RULES_ENGINE_CONSTANTS.ERR_UNKNOWN).message;
}
