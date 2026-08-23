export async function register() {
  if (process.env.NEXT_RUNTIME === 'nodejs') {
    const { initNodeTracing } = await import('@observability/core/tracing');
    initNodeTracing('web-app', '0.1.0');
  }
}
