import { router } from './trpc';
import { costRouter } from './routers/cost';
import { latencyRouter } from './routers/latency';
import { qualityRouter } from './routers/quality';
import { promptRouter } from './routers/prompt';
import { traceRouter } from './routers/trace';
import { adminRouter } from './routers/admin';
import { authRouter } from './routers/auth';

export const appRouter = router({
  cost: costRouter,
  latency: latencyRouter,
  quality: qualityRouter,
  prompt: promptRouter,
  trace: traceRouter,
  admin: adminRouter,
  auth: authRouter,
});

export type AppRouter = typeof appRouter;
