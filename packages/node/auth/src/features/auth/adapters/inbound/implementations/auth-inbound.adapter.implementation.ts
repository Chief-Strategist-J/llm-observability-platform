import type { IAuthInboundAdapter } from '../auth-inbound.adapter';
import type { IAuthInboundPort } from '../../../ports/inbound/auth-inbound.port';

export class AuthInboundAdapterImplementation implements IAuthInboundAdapter {
  constructor(private readonly inboundPort: IAuthInboundPort) {}

  async handleRequest(
    _method: string,
    _path: string,
    _body?: unknown,
    _headers?: Record<string, string>
  ): Promise<{ statusCode: number; payload: unknown }> {
    const permissions = this.inboundPort.getSystemPermissions();
    return {
      statusCode: 200,
      payload: { status: 'handled', service: 'auth-inbound-adapter', permissionsCount: permissions.length },
    };
  }
}
