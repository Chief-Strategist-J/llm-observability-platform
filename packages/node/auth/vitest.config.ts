import { defineConfig } from 'vitest/config';

export default defineConfig({
  test: {
    globals: true,
    environment: 'node',
    reporters: ['default', 'html'],
    outputFile: {
      html: './allure-results/index.html',
    },
  },
});
