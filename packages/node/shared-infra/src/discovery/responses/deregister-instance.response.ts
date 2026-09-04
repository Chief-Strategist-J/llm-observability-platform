export interface DeregisterInstanceResponse {
  success: boolean;
  statusCode?: number;
  data?: {
    status: string;
  };
  error?: {
    code: string;
    message: string;
  };
}
