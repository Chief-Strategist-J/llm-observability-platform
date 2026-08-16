import type { AuthService } from '../../../../features/auth/service';
import type { ForgotPasswordInput, ResetPasswordInput, ChangePasswordInput } from '../../../../features/auth/types';

export async function handleForgotPassword(service: AuthService, body: unknown): Promise<unknown> {
  const input = body as ForgotPasswordInput;
  return service.forgotPassword(input);
}

export async function handleResetPassword(service: AuthService, body: unknown): Promise<unknown> {
  const input = body as ResetPasswordInput;
  await service.resetPassword(input);
  return { success: true };
}

export async function handleChangePassword(service: AuthService, userId: string, body: unknown): Promise<unknown> {
  const input = body as ChangePasswordInput;
  await service.changePassword(userId, input);
  return { success: true };
}
