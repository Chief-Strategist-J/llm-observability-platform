import type { NextConfig } from 'next';

const nextConfig: NextConfig = {
  experimental: {
    instrumentationHook: true,
  },
  transpilePackages: [
    '@observability/core',
    '@observability/design-tokens',
    '@observability/api-types',
    '@observability/realtime-sdk',
  ],
  eslint: {
    ignoreDuringBuilds: true,
  },
  typescript: {
    ignoreBuildErrors: true,
  },
  async headers() {
    return [
      {
        source: '/:path*',
        headers: [
          { key: 'Access-Control-Allow-Credentials', value: 'true' },
          { key: 'Access-Control-Allow-Origin', value: '*' },
          { key: 'Access-Control-Allow-Methods', value: 'GET,DELETE,PATCH,POST,PUT,OPTIONS' },
          { key: 'Access-Control-Allow-Headers', value: 'X-CSRF-Token, X-Requested-With, Accept, Accept-Version, Content-Length, Content-MD5, Content-Type, Date, X-Api-Version, Authorization, traceparent, tracestate, x-request-id, x-correlation-id, x-causation-id, x-idempotency-key, x-tenant-id, x-client-id, x-user-id, x-api-key' },
        ],
      },
    ];
  },
};

export default nextConfig;
