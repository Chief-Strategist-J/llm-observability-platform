import { describe, it, expect } from 'vitest';
import * as fs from 'fs';
import * as path from 'path';
import { AUTH_ENDPOINTS } from '../../src/shared/constants/endpoints';

describe('Auth OpenAPI Contract Compliance', () => {
  it('should verify contracts/openapi/v1.yaml exists and matches declared endpoints and schemas', () => {
    const contractPath = fs.existsSync(path.join(process.cwd(), 'contracts/openapi/v1.yaml'))
      ? path.join(process.cwd(), 'contracts/openapi/v1.yaml')
      : path.join(process.cwd(), 'packages/node/auth/contracts/openapi/v1.yaml');
    expect(fs.existsSync(contractPath)).toBe(true);

    const content = fs.readFileSync(contractPath, 'utf8');
    expect(content).toContain('openapi: 3.0.3');
    expect(content).toContain(AUTH_ENDPOINTS.SIGN_UP);
    expect(content).toContain(AUTH_ENDPOINTS.SIGN_IN);
    expect(content).toContain(AUTH_ENDPOINTS.SESSION);
    expect(content).toContain(AUTH_ENDPOINTS.FORGOT_PASSWORD);
    expect(content).toContain(AUTH_ENDPOINTS.RESET_PASSWORD);
    expect(content).toContain(AUTH_ENDPOINTS.CHANGE_PASSWORD);
    expect(content).toContain(AUTH_ENDPOINTS.API_KEYS);
    expect(content).toContain(AUTH_ENDPOINTS.API_KEYS_VERIFY);
    expect(content).toContain(AUTH_ENDPOINTS.PERMISSIONS);
    expect(content).toContain(AUTH_ENDPOINTS.AUDIT_LOGS);
    expect(content).toContain('SignUpRequest');
    expect(content).toContain('SignInRequest');
    expect(content).toContain('CreateApiKeyRequest');
    expect(content).toContain('VerifyApiKeyRequest');
    expect(content).toContain('X-CSRF-Token');
  });
});
