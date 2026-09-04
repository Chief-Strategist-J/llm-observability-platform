export interface ServiceInstanceDto {
  id?: string;
  name: string;
  host: string;
  port: number;
  protocol: string;
  version?: string;
  weight?: number;
  metadata?: Record<string, string>;
}

export interface ResolveServiceResponseData {
  service: string;
  endpoint: string;
  instances: ServiceInstanceDto[];
}

export interface ResolveServiceResponse {
  success: boolean;
  statusCode?: number;
  data?: ResolveServiceResponseData;
  error?: {
    code: string;
    message: string;
  };
}
