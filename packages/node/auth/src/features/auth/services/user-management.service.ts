import type { AuthRepositoryPort } from '../repository';
import type { AuthUserRecord, UpdateUserProfileInput, InviteUserInput, UpdateUserRoleInput, UpdateUserPermissionsInput, CreateUserInput } from '../types';
import { UpdateUserProfileInputSchema, InviteUserInputSchema, UpdateUserRoleInputSchema, UpdateUserPermissionsInputSchema, CreateUserInputSchema } from '../schema/auth.schema';
import { UserAlreadyExistsError, ValidationError } from '../../../shared/errors/auth.errors';
import { hashPassword } from '../../../shared/utils/argon2.util';
import { AUTH_CONSTANTS } from '../../../shared/constants/auth.constants';

export class UserManagementDomainService {
  constructor(private readonly repo: AuthRepositoryPort) {}

  async listUsers(orgId: string): Promise<AuthUserRecord[]> {
    return this.repo.listUsersByOrgId(orgId);
  }

  async getUserById(userId: string): Promise<AuthUserRecord> {
    const user = await this.repo.findUserById(userId);
    if (!user) throw new ValidationError('User not found');
    return user;
  }

  async getMyProfile(userId: string): Promise<AuthUserRecord> {
    return this.getUserById(userId);
  }

  async updateMyProfile(userId: string, input: UpdateUserProfileInput): Promise<AuthUserRecord> {
    const validated = UpdateUserProfileInputSchema.parse(input);
    await this.repo.updateUserProfile(userId, validated);
    return this.getUserById(userId);
  }

  async inviteUser(input: InviteUserInput, orgId: string, orgName: string): Promise<AuthUserRecord> {
    const validated = InviteUserInputSchema.parse(input);

    const existingUser = await this.repo.findUserByEmail(validated.email);
    if (existingUser) {
      throw new UserAlreadyExistsError(validated.email);
    }

    const tempPassword = `Tmp_${Math.random().toString(36).substring(2, 10)}!1A`;
    const passwordHash = await hashPassword(tempPassword);
    const userId = `usr_${Math.random().toString(36).substring(2, 9)}`;

    const userRecord: AuthUserRecord = {
      id: userId,
      email: validated.email,
      password_hash: passwordHash,
      name: validated.name,
      org_id: orgId,
      org_name: orgName,
      role: validated.role ?? AUTH_CONSTANTS.ROLE_MEMBER,
      blocked: false,
      user_permissions: validated.permissions ?? [],
    };

    await this.repo.createUser(userRecord);
    return userRecord;
  }

  async updateUserRole(userId: string, input: UpdateUserRoleInput): Promise<void> {
    const validated = UpdateUserRoleInputSchema.parse(input);
    await this.repo.updateUserRole(userId, validated.role);
  }

  async getUserPermissions(userId: string): Promise<string[]> {
    const user = await this.repo.findUserById(userId);
    if (!user) throw new ValidationError('User not found');
    return user.user_permissions;
  }

  async updateUserPermissions(userId: string, input: UpdateUserPermissionsInput): Promise<void> {
    const validated = UpdateUserPermissionsInputSchema.parse(input);
    await this.repo.updateUserPermissions(userId, validated.permissions);
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

  async unblockUser(userId: string): Promise<void> {
    await this.repo.unblockUser(userId);
  }

  async deleteUser(userId: string): Promise<void> {
    await this.repo.deleteUser(userId);
  }
}
