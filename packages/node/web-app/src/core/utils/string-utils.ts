/**
 * String normalization and unauthorized error classification utilities.
 */

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
