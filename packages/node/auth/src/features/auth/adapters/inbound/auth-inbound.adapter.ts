export interface IAuthInboundAdapter {
  handleRequest(
    method: string,
    path: string,
    body?: unknown,
    headers?: Record<string, string>
  ): Promise<{ statusCode: number; payload: unknown }>;
}
