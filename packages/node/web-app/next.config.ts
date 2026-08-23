import type { NextConfig } from 'next';

const nextConfig: NextConfig = {
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
};

export default nextConfig;
