import { fetchRequestHandler } from '@trpc/server/adapters/fetch';
import { appRouter } from '../../../../server/trpc/root';
import { createContext } from '../../../../server/trpc/context';

const handler: (req: Request) => Promise<Response> = (req: Request) =>
  fetchRequestHandler({
    endpoint: '/api/trpc',
    req,
    router: appRouter,
    createContext,
  });

export const GET: (req: Request) => Promise<Response> = handler;
export const POST: (req: Request) => Promise<Response> = handler;
