import * as http from 'http';
import { AuthService } from './features/auth/service';
import { AuthRestV1Router } from './api/rest/v1/router';
import { AlloyDBOmniAuthAdapter } from './infra/adapters/postgres/alloydb-omni-auth.adapter';
import { RealPostgresAuthAdapter } from './infra/adapters/postgres/real-postgres-auth.adapter';
import { AuthInboundPortImplementation } from './features/auth/ports/inbound/implementations/auth-inbound.port.implementation';
import { AuthOutboundPortImplementation } from './features/auth/ports/outbound/implementations/auth-outbound.port.implementation';
import { AuthInboundAdapterImplementation } from './features/auth/adapters/inbound/implementations/auth-inbound.adapter.implementation';
import { AuthOutboundAdapterImplementation } from './features/auth/adapters/outbound/implementations/auth-outbound.adapter.implementation';
import { AUTH_CONSTANTS } from './shared/constants/auth.constants';

const port = process.env.PORT ? parseInt(process.env.PORT, 10) : AUTH_CONSTANTS.DEFAULT_PORT;

const repositoryAdapter = (process.env.DATABASE_URL || process.env.USE_REAL_DB === 'true')
  ? new RealPostgresAuthAdapter()
  : new AlloyDBOmniAuthAdapter();
export const outboundAdapter = new AuthOutboundAdapterImplementation(repositoryAdapter);
export const outboundPort = new AuthOutboundPortImplementation(outboundAdapter);

export const service = new AuthService(outboundPort);

export const inboundPort = new AuthInboundPortImplementation(service);
export const inboundAdapter = new AuthInboundAdapterImplementation(inboundPort);

export const router = new AuthRestV1Router(service);

const server = http.createServer((req, res) => {
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
      } else if (Array.isArray(val) && val.length > 0 && val[0]) {
        headersRecord[key.toLowerCase()] = val[0];
      }
    }

    const parsedUrl = new URL(url, `http://localhost:${port}`);
    const path = parsedUrl.pathname;
    const queryParams: Record<string, string> = {};
    parsedUrl.searchParams.forEach((value, key) => { queryParams[key] = value; });

    const { statusCode, payload } = await router.route(method, path, parsedBody, headersRecord, queryParams);
    res.writeHead(statusCode, {
      'Content-Type': AUTH_CONSTANTS.HEADERS.CONTENT_TYPE_JSON,
      ...AUTH_CONSTANTS.SECURITY_CONFIG.CORS_HEADERS,
    });
    res.end(JSON.stringify(payload, null, 2));
  });
});

process.on('unhandledRejection', (reason) => {
  console.error('[Unhandled Rejection]', reason);
});
process.on('uncaughtException', (err) => {
  console.error('[Uncaught Exception]', err);
});

server.listen(port, () => {
  console.log(`[${AUTH_CONSTANTS.SERVICE_NAME}] Auth HTTP Service running live on http://localhost:${port}`);
});
