// Input Validation Utilities

/**
 * Validates that a string is not null, undefined, or empty
 * Strict validation with explicit null handling and deterministic error messages
 */
export function validateNonEmptyString(value: unknown): string {
  if (value === null) {
    throw new Error('Value cannot be null');
  }
  if (value === undefined) {
    throw new Error('Value cannot be undefined');
  }
  if (typeof value !== 'string') {
    throw new Error('Value must be a string');
  }
  if (value.trim() === '') {
    throw new Error('String cannot be empty');
  }
  return value;
}

/**
 * Validates that a number is within acceptable range
 * Explicit type checking and boundary validation with deterministic error messages
 */
export function validateNumberRange(
  value: unknown,
  min: number,
  max: number,
  fieldName: string = 'Value'
): number {
  if (value === null) {
    throw new Error(`${fieldName} cannot be null`);
  }
  if (value === undefined) {
    throw new Error(`${fieldName} cannot be undefined`);
  }
  if (typeof value !== 'number') {
    throw new Error(`${fieldName} must be a number`);
  }
  if (isNaN(value)) {
    throw new Error(`${fieldName} cannot be NaN`);
  }
  if (value < min) {
    throw new Error(`${fieldName} ${value} is below minimum ${min}`);
  }
  if (value > max) {
    throw new Error(`${fieldName} ${value} is above maximum ${max}`);
  }
  return value;
}

/**
 * Validates API response status with explicit null checking
 * Follows strict null handling rules with deterministic error messages
 */
export function validateApiResponse(response: Response): void {
  if (response === null) {
    throw new Error('Response cannot be null');
  }
  if (response === undefined) {
    throw new Error('Response cannot be undefined');
  }
  if (!response.ok) {
    throw new Error(`API request failed with status ${response.status}`);
  }
}

/**
 * Safe type guard for checking if object has required properties
 * Explicit null and type validation with deterministic error messages
 */
export function validateObjectProperties<T extends Record<string, unknown>>(
  obj: unknown,
  requiredKeys: (keyof T)[]
): T {
  if (obj === null) {
    throw new Error('Object cannot be null');
  }
  if (obj === undefined) {
    throw new Error('Object cannot be undefined');
  }
  if (typeof obj !== 'object') {
    throw new Error('Value must be an object');
  }

  const objAsRecord = obj as Record<string, unknown>;

  for (const key of requiredKeys) {
    if (!(key in objAsRecord)) {
      throw new Error(`Missing required property: ${String(key)}`);
    }
  }

  return obj as T;
}
