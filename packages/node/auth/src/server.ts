import * as http from 'http';
import { AuthService } from './features/auth/service';
import { AuthRestV1Router } from './api/rest/v1/router';
import { AlloyDBOmniAuthAdapter } from './infra/adapters/postgres/alloydb-omni-auth.adapter';
import { AUTH_CONSTANTS } from './shared/constants/auth.constants';

const port = process.env.PORT ? parseInt(process.env.PORT, 10) : 3001;
const repository = new AlloyDBOmniAuthAdapter();
const service = new AuthService(repository);
const router = new AuthRestV1Router(service);

const server = http.createServer(async (req, res) => {
  const method = req.method ?? 'GET';
  const url = req.url ?? '/';

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

    const { statusCode, payload } = await router.route(method, url, parsedBody, headersRecord);
    res.writeHead(statusCode, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify(payload, null, 2));
  });
});

server.listen(port, () => {
  console.log(`[${AUTH_CONSTANTS.SERVICE_NAME}] Auth HTTP Service running live on http://localhost:${port}`);
});
