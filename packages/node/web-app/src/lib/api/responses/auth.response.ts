import type { AuthUser } from './user.response';

export interface AuthResponse {
  user?: AuthUser;
  token?: string;
  status?: string;
  message?: string;
  payload?: any;
}

export interface GenericStatusResponse {
  success: boolean;
  message?: string;
}
