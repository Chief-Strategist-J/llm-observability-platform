export interface HeartbeatInstanceResponse {
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
