import { describe, it, expect, beforeEach } from 'vitest';
import { SecurityEngine, EnvSecretStoreAdapter } from '../../src/shared/utils/security.util';
import { hashPassword, verifyPassword } from '../../src/shared/utils/argon2.util';
import { SignUpInputSchema } from '../../src/features/auth/schema/auth.schema';
import { AUTH_QUERIES } from '../../src/features/auth/queries/auth.queries';
import { AUTH_CONSTANTS } from '../../src/shared/constants/auth.constants';

describe('Allure Gold Standard Test Suite: 13-Pillar Security Hardening', () => {
  let security: SecurityEngine;

  beforeEach(() => {
    security = new SecurityEngine();
  });

  it('1. Password Hashing: should securely hash and verify password via Argon2id', async () => {
    const plain = 'StrongPass123!';
    const hash = await hashPassword(plain);
    expect(hash).not.toEqual(plain);
    const valid = await verifyPassword(plain, hash);
    expect(valid).toBe(true);
    const invalid = await verifyPassword('WrongPass123!', hash);
    expect(invalid).toBe(false);
  });

  it('2. Token Revocation: should revoke session token and report revocation status', () => {
    const token = 'token-to-revoke-123';
    expect(security.isTokenRevoked(token)).toBe(false);
    security.revokeToken(token);
    expect(security.isTokenRevoked(token)).toBe(true);
  });

  it('3. Brute-Force Protection: should lock out account after 5 failed login attempts', () => {
    const email = 'target@observability.io';
    expect(security.checkBruteForceLockout(email)).toBe(false);
    for (let i = 0; i < 4; i++) {
      security.recordFailedAttempt(email);
      expect(security.checkBruteForceLockout(email)).toBe(false);
    }
    security.recordFailedAttempt(email);
    expect(security.checkBruteForceLockout(email)).toBe(true);
    security.clearFailedAttempts(email);
    expect(security.checkBruteForceLockout(email)).toBe(false);
  });

  it('4. Rate Limiting: should block request rate when sliding window threshold exceeded', () => {
    const key = 'ip:192.168.1.1';
    for (let i = 0; i < 5; i++) {
      expect(security.checkRateLimit(key, 5, 1000)).toBe(true);
    }
    expect(security.checkRateLimit(key, 5, 1000)).toBe(false);
  });

  it('5. Input Validation: should enforce strict email format and password complexity via Zod', () => {
    const invalidInput = {
      email: 'bad-email',
      password: 'weak',
      name: 'A',
      organization_name: 'B',
    };
    expect(() => SignUpInputSchema.parse(invalidInput)).toThrow();

    const validInput = {
      email: 'valid@observability.io',
      password: 'StrongPass123!',
      name: 'Valid User',
      organization_name: 'Valid Org',
      role: AUTH_CONSTANTS.ROLE_ADMIN,
    };
    const parsed = SignUpInputSchema.parse(validInput);
    expect(parsed.email).toBe('valid@observability.io');
  });

  it('6. CSRF Protection: should generate and verify anti-CSRF double-submit token', () => {
    const sessionId = 'session-999';
    const csrfToken = security.generateCsrfToken(sessionId);
    expect(csrfToken.startsWith('csrf_session-999_')).toBe(true);
    expect(security.verifyCsrfToken(csrfToken, csrfToken)).toBe(true);
    expect(security.verifyCsrfToken('invalid-csrf', csrfToken)).toBe(false);
  });

  it('7. XSS Protection: should sanitize HTML script tags and control characters', () => {
    const xssPayload = '<script>alert("xss")</script>';
    const sanitized = security.sanitizeHtml(xssPayload);
    expect(sanitized).not.toContain('<script>');
    expect(sanitized).toContain('&lt;script&gt;');
  });

  it('8. SQL Injection Protection: should enforce parameterized query placeholders', () => {
    const query = AUTH_QUERIES.FLOW_SIGN_IN.FIND_USER_BY_EMAIL;
    expect(query).toContain('$1');
    expect(query).not.toContain("''");
  });

  it('9. Secrets Management: should fetch secrets via injected SecretStorePort adapter', async () => {
    process.env.TEST_SECRET_KEY = 'secret-value-123';
    const secretStore = new EnvSecretStoreAdapter();
    const val = await secretStore.getSecret('TEST_SECRET_KEY');
    expect(val).toBe('secret-value-123');
  });

  it('10. Credential-Stuffing Protection: should flag IP attempting logins across >5 accounts', () => {
    const ip = '10.0.0.50';
    for (let i = 0; i < 5; i++) {
      expect(security.detectCredentialStuffing(ip, `user${i}@acme.com`)).toBe(false);
    }
    expect(security.detectCredentialStuffing(ip, 'user5@acme.com')).toBe(true);
  });

  it('11. Device / Session Tracking: should register and track device fingerprints per user', () => {
    const userId = 'usr-device-100';
    const result1 = security.registerAndDetectAnomaly(userId, 'device-macbook-pro');
    expect(result1.isAnomaly).toBe(false);
  });

  it('12. IP / Device Anomaly Detection: should flag login from unrecognized new device', () => {
    const userId = 'usr-device-200';
    security.registerAndDetectAnomaly(userId, 'known-laptop');
    const anomalyResult = security.registerAndDetectAnomaly(userId, 'unknown-phone');
    expect(anomalyResult.isAnomaly).toBe(true);
  });

  it('13. Step-Up Authentication: should generate and verify OTP for step-up auth', () => {
    const userId = 'usr-mfa-300';
    const otp = security.generateStepUpOtp(userId);
    expect(otp.length).toBe(6);
    expect(security.verifyStepUpOtp(userId, '000000')).toBe(false);
    expect(security.verifyStepUpOtp(userId, otp)).toBe(true);
  });
});
