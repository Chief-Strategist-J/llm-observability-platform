import { RawAuthApiClient } from '../../../../src/lib/api/auth-client';

export class AuthApiClient {
  private rawClient: RawAuthApiClient;

  constructor(baseUrl = 'http://localhost:3001') {
    this.rawClient = new RawAuthApiClient(baseUrl);
  }

  async verifyUserExistsServerSide(email: string): Promise<boolean> {
    try {
      await this.rawClient.signUp({
        name: 'Check User',
        organization_name: 'Check Org',
        email,
        password: 'Password123!',
      });
      return false;
    } catch (err: any) {
      return err.message?.includes('already exists') || err.message?.includes('duplicate');
    }
  }

  async directSignUp(payload: any): Promise<any> {
    return await this.rawClient.signUp(payload);
  }

  async directSignIn(credentials: { email: string; password: string }): Promise<any> {
    return await this.rawClient.signIn(credentials);
  }
}

export const authApiClient = new AuthApiClient();
