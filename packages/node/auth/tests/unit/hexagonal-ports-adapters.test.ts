import { describe, it, expect, beforeEach } from 'vitest';
import { AlloyDBOmniAuthAdapter } from '../../src/infra/adapters/postgres/alloydb-omni-auth.adapter';
import { AuthOutboundAdapterImplementation } from '../../src/features/auth/adapters/outbound/implementations/auth-outbound.adapter.implementation';
import { AuthOutboundPortImplementation } from '../../src/features/auth/ports/outbound/implementations/auth-outbound.port.implementation';
import { AuthService } from '../../src/features/auth/service';
import { AuthInboundPortImplementation } from '../../src/features/auth/ports/inbound/implementations/auth-inbound.port.implementation';
import { AuthInboundAdapterImplementation } from '../../src/features/auth/adapters/inbound/implementations/auth-inbound.adapter.implementation';
import { AUTH_CONSTANTS } from '../../src/shared/constants/auth.constants';

describe('Hexagonal Ports & Adapters Architecture Unit Tests', () => {
  let dbAdapter: AlloyDBOmniAuthAdapter;
  let outboundAdapter: AuthOutboundAdapterImplementation;
  let outboundPort: AuthOutboundPortImplementation;
  let service: AuthService;
  let inboundPort: AuthInboundPortImplementation;
  let inboundAdapter: AuthInboundAdapterImplementation;

  beforeEach(() => {
    dbAdapter = new AlloyDBOmniAuthAdapter();
    outboundAdapter = new AuthOutboundAdapterImplementation(dbAdapter);
    outboundPort = new AuthOutboundPortImplementation(outboundAdapter);
    service = new AuthService(outboundPort);
    inboundPort = new AuthInboundPortImplementation(service);
    inboundAdapter = new AuthInboundAdapterImplementation(inboundPort);
  });

  it('should flow sign-in request through Hexagonal Inbound & Outbound Ports', async () => {
    const signInResult = await inboundPort.signIn({
      email: AUTH_CONSTANTS.DEFAULT_ADMIN_EMAIL,
      password: 'password123',
      ip_address: '127.0.0.1',
      user_agent: 'VitestHexagonal/1.0',
    });

    expect(signInResult.token).toBeDefined();
    expect(signInResult.payload.email).toBe(AUTH_CONSTANTS.DEFAULT_ADMIN_EMAIL);
    expect(signInResult.user.role).toBe(AUTH_CONSTANTS.ROLE_ADMIN);
  });

  it('should validate session through Inbound Port', async () => {
    const signInResult = await inboundPort.signIn({
      email: AUTH_CONSTANTS.DEFAULT_ADMIN_EMAIL,
      password: 'password123',
      ip_address: '127.0.0.1',
      user_agent: 'VitestHexagonal/1.0',
    });

    const session = await inboundPort.validateSession(signInResult.token);
    expect(session.sub).toBe(AUTH_CONSTANTS.DEFAULT_ADMIN_ID);
  });

  it('should execute handleRequest on Inbound Adapter delegating to Inbound Port', async () => {
    const response = await inboundAdapter.handleRequest('GET', '/api/v1/system/permissions');
    expect(response.statusCode).toBe(200);
    expect(response.payload).toHaveProperty('permissionsCount');
  });

  it('should delegate repository operations directly through Outbound Port', async () => {
    const user = await outboundPort.findUserByEmail(AUTH_CONSTANTS.DEFAULT_ADMIN_EMAIL);
    expect(user).not.toBeNull();
    expect(user?.email).toBe(AUTH_CONSTANTS.DEFAULT_ADMIN_EMAIL);
  });
});
