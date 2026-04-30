// Centralized Error Handling

/**
 * Standardized error class for API errors
 * Follows strict type safety and null handling rules
 */
export class ApiError extends Error {
  constructor(
    message: string,
    public readonly status?: number,
    public readonly endpoint?: string
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

/**
 * Standardized error class for validation errors
 * Follows strict type safety and null handling rules
 */
export class ValidationError extends Error {
  constructor(
    message: string,
    public readonly field?: string
  ) {
    super(message);
    this.name = 'ValidationError';
  }
}

/**
 * Centralized error handler for API calls
 * Explicit null checking and deterministic error handling
 */
export function handleApiError(
  error: unknown,
  endpoint: string,
  context: string
): ApiError {
  if (error === null) {
    return new ApiError(`${context}: Null error occurred`, undefined, endpoint);
  }
  if (error === undefined) {
    return new ApiError(`${context}: Undefined error occurred`, undefined, endpoint);
  }
  
  if (error instanceof ApiError) {
    return error;
  }

  if (error instanceof Error) {
    return new ApiError(`${context}: ${error.message}`, undefined, endpoint);
  }

  if (typeof error === 'string') {
    return new ApiError(`${context}: ${error}`, undefined, endpoint);
  }

  return new ApiError(
    `${context}: Unknown error occurred`,
    undefined,
    endpoint
  );
}

/**
 * Safe async wrapper that converts exceptions to standardized errors
 * Strict null handling and explicit error conversion
 */
export async function safeAsyncCall<T>(
  operation: () => Promise<T>,
  errorMessage: string,
  endpoint?: string
): Promise<T> {
  try {
    return await operation();
  } catch (error) {
    throw handleApiError(error, endpoint || 'unknown', errorMessage);
  }
}
