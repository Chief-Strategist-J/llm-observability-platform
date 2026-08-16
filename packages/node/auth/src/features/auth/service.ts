import type { AuthRepositoryPort } from './repository';
import type {
  SignUpInput,
  SignInInput,
  ForgotPasswordInput,
  ResetPasswordInput,
  ChangePasswordInput,
  CreateApiKeyInput,
  VerifyApiKeyInput,
  CreateOrganizationInput,
  CreateUserInput,
  AuthUserRecord,
  AuditLogRecord,
} from './types';
import type { ApiKeyRecord, AuthTokenPayload } from '../../shared/types/auth.types';
import {
  SignUpInputSchema,
  SignInInputSchema,
  ResetPasswordInputSchema,
  ChangePasswordInputSchema,
  CreateApiKeyInputSchema,
  VerifyApiKeyInputSchema,
  CreateOrganizationInputSchema,
  CreateUserInputSchema,
} from './schema/auth.schema';
import {
  InvalidCredentialsError,
  UserBlockedError,
  ApiKeyRevokedError,
  UserAlreadyExistsError,
  OrgAlreadyExistsError,
  InsufficientPermissionError,
  ValidationError,
} from '../../shared/errors/auth.errors';
import { hashPassword, verifyPassword, hashApiKey } from '../../shared/utils/argon2.util';
import { createToken, verifyToken } from '../../shared/utils/jwt.util';
import { AUTH_CONSTANTS } from '../../shared/constants/auth.constants';

export class AuthService {
  constructor(private readonly repo: AuthRepositoryPort) {}

  async createOrganization(input: CreateOrganizationInput): Promise<{ id: string; name: string; slug: string }> {
    const validated = CreateOrganizationInputSchema.parse(input);
    const orgId = `org_${Math.random().toString(36).substring(2, 9)}`;
    const slug = validated.slug ?? validated.name.toLowerCase().replace(/[^a-z0-9]+/g, '-');

    try {
      await this.repo.createOrganization({ id: orgId, name: validated.name, slug });
    } catch (err: any) {
      if (err.message?.includes('Organization name already exists')) {
        throw new OrgAlreadyExistsError(validated.name);
      }
      throw err;
    }

    return { id: orgId, name: validated.name, slug };
  }

  async deleteOrganization(orgId: string): Promise<void> {
    await this.repo.deleteOrganization(orgId);
  }

  async createUser(input: CreateUserInput): Promise<AuthUserRecord> {
    const validated = CreateUserInputSchema.parse(input);

    const existingUser = await this.repo.findUserByEmail(validated.email);
    if (existingUser) {
      throw new UserAlreadyExistsError(validated.email);
    }

    const passwordHash = await hashPassword(validated.password);
    const userId = `usr_${Math.random().toString(36).substring(2, 9)}`;

    const userRecord: AuthUserRecord = {
      id: userId,
      email: validated.email,
      password_hash: passwordHash,
      name: validated.name,
      org_id: validated.org_id,
      org_name: '',
      role: validated.role ?? AUTH_CONSTANTS.ROLE_MEMBER,
      blocked: false,
      user_permissions: validated.permissions ?? [],
    };

    await this.repo.createUser(userRecord);
    return userRecord;
  }

  async blockUser(userId: string): Promise<void> {
    await this.repo.blockUser(userId);
  }

  async deleteUser(userId: string): Promise<void> {
    await this.repo.deleteUser(userId);
  }

  async purgeExpiredSoftDeletes(): Promise<number> {
    return this.repo.purgeExpiredSoftDeletes();
  }

  async signUp(input: SignUpInput): Promise<{ token: string; payload: AuthTokenPayload; user: AuthUserRecord }> {
    const validated = SignUpInputSchema.parse(input);

    const existingUser = await this.repo.findUserByEmail(validated.email);
    if (existingUser) {
      throw new UserAlreadyExistsError(validated.email);
    }

    const passwordHash = await hashPassword(validated.password);
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

    const isValid = await verifyPassword(validated.password, user.password_hash);
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
    return { token, payload, user };
  }

  async validateSession(token: string): Promise<AuthTokenPayload> {
    return verifyToken(token);
  }

  async forgotPassword(input: ForgotPasswordInput): Promise<{ resetToken: string }> {
    const user = await this.repo.findUserByEmail(input.email);
    if (!user) {
      return { resetToken: '' };
    }

    const rawToken = `rst_${Math.random().toString(36).substring(2, 15)}`;
    const tokenHash = await hashApiKey(rawToken);
    const expiresAtMs = Date.now() + 3600000;

    await this.repo.savePasswordResetToken(tokenHash, user.id, expiresAtMs);
    return { resetToken: rawToken };
  }

  async resetPassword(input: ResetPasswordInput): Promise<void> {
    const validated = ResetPasswordInputSchema.parse(input);
    const tokenHash = await hashApiKey(validated.token);

    const record = await this.repo.findPasswordResetToken(tokenHash);
    if (!record || record.used || record.expiresAtMs < Date.now()) {
      throw new ValidationError('Invalid or expired password reset token');
    }

    const newHash = await hashPassword(validated.new_password);
    await this.repo.updateUserPassword(record.userId, newHash);
    await this.repo.markPasswordResetTokenUsed(tokenHash);
  }

  async changePassword(userId: string, input: ChangePasswordInput): Promise<void> {
    const validated = ChangePasswordInputSchema.parse(input);
    const user = await this.repo.findUserById(userId);
    if (!user) {
      throw new InvalidCredentialsError();
    }

    const isValid = await verifyPassword(validated.current_password, user.password_hash);
    if (!isValid) {
      throw new InvalidCredentialsError();
    }

    const newHash = await hashPassword(validated.new_password);
    await this.repo.updateUserPassword(user.id, newHash);
  }

  async generateApiKey(input: CreateApiKeyInput): Promise<{ rawKey: string; keyRecord: ApiKeyRecord }> {
    const validated = CreateApiKeyInputSchema.parse(input);

    let prefix: string = AUTH_CONSTANTS.API_KEY_PREFIX_GENERAL;
    if (validated.key_type === AUTH_CONSTANTS.KEY_TYPE_SUPER_SECRET) {
      prefix = AUTH_CONSTANTS.API_KEY_PREFIX_SUPER_SECRET;
    } else if (validated.key_type === AUTH_CONSTANTS.KEY_TYPE_TESTING) {
      prefix = AUTH_CONSTANTS.API_KEY_PREFIX_TESTING;
    }

    const keyId = `key_${Math.random().toString(36).substring(2, 9)}`;
    const secret = Math.random().toString(36).substring(2, 15) + Math.random().toString(36).substring(2, 15);
    const rawKey = `${prefix}${validated.org_id}_${secret}`;
    const keyHash = await hashApiKey(rawKey);

    const keyRecord: ApiKeyRecord = {
      key_id: keyId,
      org_id: validated.org_id,
      key_type: validated.key_type,
      key_hash: keyHash,
      prefix,
      name: validated.name,
      permissions: validated.permissions,
      created_at_ms: Date.now(),
      revoked: false,
    };

    await this.repo.saveApiKey(keyRecord);
    return { rawKey, keyRecord };
  }

  async verifyApiKey(input: VerifyApiKeyInput): Promise<{ valid: boolean; record: ApiKeyRecord; authorized: boolean }> {
    const validated = VerifyApiKeyInputSchema.parse(input);
    const keyHash = await hashApiKey(validated.key);
    const record = await this.repo.findApiKeyByHash(keyHash);

    if (!record || record.revoked) {
      throw new ApiKeyRevokedError();
    }

    let authorized = true;
    if (validated.required_permission) {
      const isSuperSecret = record.key_type === AUTH_CONSTANTS.KEY_TYPE_SUPER_SECRET;
      const hasAdminAll = record.permissions.includes(AUTH_CONSTANTS.PERMISSION_ADMIN_ALL);
      const hasSpecific = record.permissions.includes(validated.required_permission);
      authorized = isSuperSecret || hasAdminAll || hasSpecific;

      if (!authorized) {
        throw new InsufficientPermissionError(validated.required_permission);
      }
    }

    return { valid: true, record, authorized };
  }

  async fetchUserAuditLogs(userId: string): Promise<AuditLogRecord[]> {
    return this.repo.fetchUserAuditLogs(userId);
  }

  getSystemPermissions(): string[] {
    return [
      AUTH_CONSTANTS.PERMISSION_TRACES_READ,
      AUTH_CONSTANTS.PERMISSION_TRACES_WRITE,
      AUTH_CONSTANTS.PERMISSION_METRICS_READ,
      AUTH_CONSTANTS.PERMISSION_METRICS_WRITE,
      AUTH_CONSTANTS.PERMISSION_LOGS_READ,
      AUTH_CONSTANTS.PERMISSION_LOGS_WRITE,
      AUTH_CONSTANTS.PERMISSION_ALERTS_READ,
      AUTH_CONSTANTS.PERMISSION_ALERTS_WRITE,
      AUTH_CONSTANTS.PERMISSION_ADMIN_ALL,
    ];
  }
}
