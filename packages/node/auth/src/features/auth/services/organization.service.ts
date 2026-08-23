import type { AuthRepositoryPort, OrganizationRecord } from '../repository';
import type { CreateOrganizationInput, UpdateOrganizationInput } from '../types';
import type { AuthTokenPayload } from '../../../shared/types/auth.types';
import { CreateOrganizationInputSchema, UpdateOrganizationInputSchema } from '../schema/auth.schema';
import { OrgAlreadyExistsError, InsufficientPermissionError, InvalidCredentialsError, ValidationError } from '../../../shared/errors/auth.errors';
import { verifyToken, createToken } from '../../../shared/utils/jwt.util';
import { AUTH_CONSTANTS } from '../../../shared/constants/auth.constants';

export class OrganizationDomainService {
  constructor(private readonly repo: AuthRepositoryPort) {}

  async listOrganizations(userId: string): Promise<OrganizationRecord[]> {
    return this.repo.listOrganizationsByUserId(userId);
  }

  async getOrganization(orgId: string): Promise<OrganizationRecord> {
    const org = await this.repo.getOrganizationById(orgId);
    if (!org) throw new ValidationError('Organization not found');
    return org;
  }

  async createOrganization(input: CreateOrganizationInput, creatorUserId?: string): Promise<{ id: string; name: string; slug: string }> {
    const validated = CreateOrganizationInputSchema.parse(input);
    const orgId = `org_${Math.random().toString(36).substring(2, 9)}`;
    const slug = validated.slug ?? validated.name.toLowerCase().replace(/[^a-z0-9]+/g, '-');

    try {
      await this.repo.createOrganization({ id: orgId, name: validated.name, slug }, creatorUserId);
    } catch (err: any) {
      if (err.message?.includes('Organization name already exists')) {
        throw new OrgAlreadyExistsError(validated.name);
      }
      throw err;
    }

    return { id: orgId, name: validated.name, slug };
  }

  async updateOrganization(orgId: string, input: UpdateOrganizationInput): Promise<OrganizationRecord> {
    const validated = UpdateOrganizationInputSchema.parse(input);
    await this.repo.updateOrganization(orgId, validated);
    const updated = await this.repo.getOrganizationById(orgId);
    if (!updated) throw new ValidationError('Organization not found');
    return updated;
  }

  async deleteOrganization(orgId: string): Promise<void> {
    await this.repo.deleteOrganization(orgId);
  }

  async switchOrganization(userId: string, targetOrgId: string, currentToken: string): Promise<{ token: string; payload: AuthTokenPayload }> {
    const orgs = await this.repo.listOrganizationsByUserId(userId);
    const target = orgs.find((o) => o.id === targetOrgId);
    if (!target) throw new InsufficientPermissionError('target organization');

    const user = await this.repo.findUserById(userId);
    if (!user) throw new InvalidCredentialsError();

    const oldPayload = verifyToken(currentToken);
    await this.repo.addTokenToDenylist(currentToken, oldPayload.exp * 1000);

    const token = createToken(user.id, user.email, {
      org_id: target.id,
      org_name: target.name,
      role: user.role,
    });
    const newPayload = verifyToken(token);

    await this.repo.recordAuditLog({
      id: `audit_${Math.random().toString(36).substring(2, 9)}`,
      user_id: userId,
      org_id: target.id,
      event_type: AUTH_CONSTANTS.AUDIT_EVENT_ORG_SWITCH,
      ip_address: '0.0.0.0',
      user_agent: 'server',
      timestamp_ms: Date.now(),
    });

    return { token, payload: newPayload };
  }
}
