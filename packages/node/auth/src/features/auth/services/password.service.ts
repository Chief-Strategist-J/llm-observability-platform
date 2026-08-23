import type { AuthRepositoryPort } from '../repository';
import type { ForgotPasswordInput, ResetPasswordInput, ChangePasswordInput } from '../types';
import { ResetPasswordInputSchema, ChangePasswordInputSchema } from '../schema/auth.schema';
import { InvalidCredentialsError, ValidationError } from '../../../shared/errors/auth.errors';
import { hashPassword, verifyPassword, hashApiKey } from '../../../shared/utils/argon2.util';

export class PasswordDomainService {
  constructor(private readonly repo: AuthRepositoryPort) {}

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
}
