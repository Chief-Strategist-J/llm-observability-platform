import { defineConfig } from 'vitest/config';

export default defineConfig({
  test: {
    globals: false,
    environment: 'node',
    include: ['tests/**/*.test.ts'],
    // Allow top-level await in test files (used for dynamic import after mocks)
    pool: 'forks',
  },
  resolve: {
    // Map .js imports to .ts sources during testing
    conditions: ['import', 'node'],
  },
});
