/* eslint-disable @typescript-eslint/no-unsafe-assignment, @typescript-eslint/no-unsafe-member-access */
import type { NextAuthConfig } from 'next-auth';
import Credentials from 'next-auth/providers/credentials';
import { AuthService, PostgresAuthAdapter } from '@observability/auth';

const authRepository = new PostgresAuthAdapter();
const authService = new AuthService(authRepository);

export const authConfig: NextAuthConfig = {
  providers: [
    Credentials({
      name: 'Credentials',
      credentials: {
        email: { label: 'Email', type: 'email' },
        password: { label: 'Password', type: 'password' },
      },
      async authorize(credentials) {
        if (!credentials?.email || !credentials?.password) return null;
        try {
          const authResult = await authService.signIn({
            email: String(credentials.email),
            password: String(credentials.password),
          });
          const payload = authResult.payload;
          return {
            id: payload.sub,
            email: payload.email,
            name: 'Observability Admin',
            org: {
              id: payload.org.org_id,
              name: payload.org.org_name,
              role: payload.org.role,
            },
          };
        } catch {
          return null;
        }
      },
    }),
  ],
  pages: {
    signIn: '/auth/sign-in',
  },
  callbacks: {
    jwt({ token, user }) {
      if (user) {
        token.org = (user as Record<string, unknown>).org;
      }
      return token;
    },
    session({ session, token }) {
      if (token?.org) {
        (session as unknown as Record<string, unknown>).org = token.org;
      }
      return session;
    },
  },
  session: { strategy: 'jwt' },
};
