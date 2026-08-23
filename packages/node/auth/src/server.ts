import * as http from 'http';
import { AuthService } from './features/auth/service';
import { AuthRestV1Router } from './api/rest/v1/router';
import { AlloyDBOmniAuthAdapter } from './infra/adapters/postgres/alloydb-omni-auth.adapter';
import { RealPostgresAuthAdapter } from './infra/adapters/postgres/real-postgres-auth.adapter';
import type { AuthRepositoryPort } from './features/auth/repository';
import { AuthEventProducer } from './shared/messaging/producers/auth-event.producer';
import { AuthEventConsumer } from './shared/messaging/consumers/auth-event.consumer';
import { AUTH_CONSTANTS } from './shared/constants/auth.constants';
import { initAuthTracing } from './infra/tracing/tracer';
import { traceHttpMiddleware } from './infra/tracing/middleware';

initAuthTracing();

const port = process.env.PORT ? parseInt(process.env.PORT, 10) : AUTH_CONSTANTS.DEFAULT_PORT;

const dbUrl = process.env.DATABASE_URL || 'postgresql://postgres:postgres@localhost:31412/observability_auth';
export const repositoryAdapter: AuthRepositoryPort = (process.env.USE_MOCK_DB === 'true')
  ? new AlloyDBOmniAuthAdapter()
  : new RealPostgresAuthAdapter(dbUrl);

export const authEventProducer = new AuthEventProducer();
export const authEventConsumer = new AuthEventConsumer();

authEventProducer.init().catch((err: any) => {
  console.warn('[kafka-producer] Operating in fallback mode:', err?.message || err);
});

authEventConsumer.init().catch((err: any) => {
  console.warn('[kafka-consumer] Operating in fallback mode:', err?.message || err);
});

export const service = new AuthService(repositoryAdapter, authEventProducer);
export const router = new AuthRestV1Router(service);

const server = http.createServer((req, res) => {
  traceHttpMiddleware(req, res, () => {
    const method = req.method ?? 'GET';
    const url = req.url ?? '/';

    if (method === 'OPTIONS') {
      res.writeHead(204, AUTH_CONSTANTS.SECURITY_CONFIG.CORS_HEADERS);
      res.end();
      return;
    }

    let bodyData = '';
    req.on('data', (chunk) => {
      bodyData += chunk.toString();
    });

    req.on('end', async () => {
      let parsedBody: unknown = undefined;
      if (bodyData) {
        try {
          parsedBody = JSON.parse(bodyData);
        } catch {
          parsedBody = bodyData;
        }
      }

      const headersRecord: Record<string, string> = {};
      for (const [key, val] of Object.entries(req.headers)) {
        if (typeof val === 'string') {
          headersRecord[key.toLowerCase()] = val;
        }
      }

      const result = await router.route(method, url, parsedBody, headersRecord);

      res.writeHead(result.statusCode, {
        ...AUTH_CONSTANTS.SECURITY_CONFIG.CORS_HEADERS,
        'Content-Type': 'application/json',
      });
      res.end(JSON.stringify(result.payload));
    });
  });
});

server.listen(port, () => {
  console.log(`[auth-service] Auth HTTP Service running live on http://localhost:${port}`);
});
