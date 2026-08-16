import { initTRPC, TRPCError } from '@trpc/server';
import superjson from 'superjson';
import type { Context } from './context';

const t = initTRPC.context<Context>().create({
  transformer: superjson,
});

export const router = t.router;
export const publicProcedure = t.procedure;
export const middleware = t.middleware;

const enforceAuth = middleware(async ({ ctx, next }) => {
  if (!ctx.session) {
    throw new TRPCError({ code: 'UNAUTHORIZED' });
  }
  return next({
    ctx: {
      session: ctx.session,
      orgId: ctx.orgId,
    },
  });
});

export const protectedProcedure = publicProcedure.use(enforceAuth);

const enforceAdmin = middleware(async ({ ctx, next }) => {
  if (!ctx.session) {
    throw new TRPCError({ code: 'UNAUTHORIZED' });
  }
  const role = ctx.session.org.role;
  if (role !== 'owner' && role !== 'admin') {
    throw new TRPCError({ code: 'FORBIDDEN' });
  }
  return next({
    ctx: {
      session: ctx.session,
      orgId: ctx.orgId,
    },
  });
});

export const adminProcedure = publicProcedure.use(enforceAdmin);
