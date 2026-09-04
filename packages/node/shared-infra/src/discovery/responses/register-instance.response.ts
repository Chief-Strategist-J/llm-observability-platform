export interface RegisterInstanceResponseData {
  id: string;
  name: string;
  status: string;
  leaseTtlSeconds: number;
}

export interface RegisterInstanceResponse {
  success: boolean;
  statusCode?: number;
  data?: RegisterInstanceResponseData;
  error?: {
    code: string;
    message: string;
  };
}
