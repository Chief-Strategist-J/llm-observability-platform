import type { AuthRepositoryPort } from '../repository';
import type { SignUpInput, SignInInput, AuthUserRecord } from '../types';
import type { AuthTokenPayload } from '../../../shared/types/auth.types';
import type { AuthEventProducer } from '../../../shared/messaging/producers/auth-event.producer';
import { SignUpInputSchema, SignInInputSchema } from '../schema/auth.schema';
import { UserAlreadyExistsError, OrgAlreadyExistsError, InvalidCredentialsError, UserBlockedError, ValidationError } from '../../../shared/errors/auth.errors';
import { hashPassword, verifyPassword } from '../../../shared/utils/argon2.util';
import { createToken, verifyToken } from '../../../shared/utils/jwt.util';
import { AUTH_CONSTANTS } from '../../../shared/constants/auth.constants';
import { withSpan } from '../../../infra/tracing/tracer';

export class UserAuthDomainService {
  constructor(
    private readonly repo: AuthRepositoryPort,
    private readonly eventProducer?: AuthEventProducer,
  ) {}

  async signUp(input: SignUpInput): Promise<{ token: string; payload: AuthTokenPayload; user: AuthUserRecord }> {
    const validated = SignUpInputSchema.parse(input);

    const existingUser = await this.repo.findUserByEmail(validated.email);
    if (existingUser) {
      throw new UserAlreadyExistsError(validated.email);
    }

    const passwordHash = await withSpan('Argon2id Password Hash', async (span) => {
      span.setAttribute('crypto.algorithm', 'argon2id');
      return hashPassword(validated.password);
    });

    const userId = `usr_${Math.random().toString(36).substring(2, 9)}`;
    const orgId = `org_${Math.random().toString(36).substring(2, 9)}`;

    const userRecord: AuthUserRecord = {
      id: userId,
      email: validated.email,
      password_hash: passwordHash,
      name: validated.name,
      org_id: orgId,
      org_name: validated.organization_name,
      role: validated.role ?? AUTH_CONSTANTS.ROLE_ADMIN,
      blocked: false,
      user_permissions: [AUTH_CONSTANTS.PERMISSION_ADMIN_ALL],
    };

    try {
      await this.repo.createOrganizationAndUser(userRecord);
    } catch (err: any) {
      if (err.message?.includes('Organization name already exists')) {
        throw new OrgAlreadyExistsError(validated.organization_name);
      }
      throw err;
    }

    const token = createToken(userRecord.id, userRecord.email, {
      org_id: userRecord.org_id,
      org_name: userRecord.org_name,
      role: userRecord.role,
    });

    const payload = verifyToken(token);
    if (this.eventProducer) {
      await this.eventProducer.publishUserSignedUp({
        userId: userRecord.id,
        email: userRecord.email,
        orgId: userRecord.org_id,
      }).catch(() => {});
    }
    return { token, payload, user: userRecord };
  }

  async signIn(input: SignInInput): Promise<{ token: string; payload: AuthTokenPayload; user: AuthUserRecord }> {
    const validated = SignInInputSchema.parse(input);

    const user = await this.repo.findUserByEmail(validated.email);
    if (!user) {
      throw new InvalidCredentialsError();
    }

    if (user.blocked) {
      throw new UserBlockedError();
    }

    const isValid = await withSpan('Argon2id Password Check', async (span) => {
      span.setAttribute('crypto.algorithm', 'argon2id');
      return verifyPassword(validated.password, user.password_hash);
    });

    if (!isValid) {
      throw new InvalidCredentialsError();
    }

    await this.repo.recordAuditLog({
      id: `audit_${Math.random().toString(36).substring(2, 9)}`,
      user_id: user.id,
      org_id: user.org_id,
      event_type: AUTH_CONSTANTS.AUDIT_EVENT_SIGNIN,
      ip_address: validated.ip_address,
      user_agent: validated.user_agent,
      timestamp_ms: Date.now(),
    });

    const token = createToken(user.id, user.email, {
      org_id: user.org_id,
      org_name: user.org_name,
      role: user.role,
    });

    const payload = verifyToken(token);
    if (this.eventProducer) {
      await this.eventProducer.publishUserSignedIn({
        userId: user.id,
        email: user.email,
        orgId: user.org_id,
      }).catch(() => {});
    }
    return { token, payload, user };
  }

  async signOut(token: string): Promise<void> {
    const payload = verifyToken(token);
    await this.repo.addTokenToDenylist(token, payload.exp * 1000);
    await this.repo.recordAuditLog({
      id: `audit_${Math.random().toString(36).substring(2, 9)}`,
      user_id: payload.sub,
      org_id: payload.org.org_id,
      event_type: AUTH_CONSTANTS.AUDIT_EVENT_SIGNOUT,
      ip_address: '0.0.0.0',
      user_agent: 'server',
      timestamp_ms: Date.now(),
    });
  }

  async validateSession(token: string): Promise<AuthTokenPayload> {
    const isDenylisted = await this.repo.isTokenDenylisted(token);
    if (isDenylisted) throw new ValidationError('Session has been invalidated');
    return verifyToken(token);
  }
}
