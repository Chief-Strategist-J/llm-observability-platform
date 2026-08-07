import type { NextAuthConfig } from 'next-auth';
import Credentials from 'next-auth/providers/credentials';

export const authConfig: NextAuthConfig = {
  providers: [
    Credentials({
      name: 'Credentials',
      credentials: {
        email: { label: 'Email', type: 'email' },
        password: { label: 'Password', type: 'password' },
      },
      async authorize(credentials) {
        if (!credentials?.email) return null;
        return {
          id: 'usr-001-admin',
          email: credentials.email as string,
          name: 'Demo Admin',
          org: {
            id: 'org-001-default',
            name: 'Acme Corp',
            role: 'owner',
          },
        };
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
