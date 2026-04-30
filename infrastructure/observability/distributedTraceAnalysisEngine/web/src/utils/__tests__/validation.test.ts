import { validateNonEmptyString, validateNumberRange, validateApiResponse } from '../validation';

describe('Validation Utilities', () => {
  describe('validateNonEmptyString', () => {
    test('should accept valid non-empty strings', () => {
      expect(() => validateNonEmptyString('hello')).not.toThrow();
      expect(() => validateNonEmptyString('test')).not.toThrow();
    });

    test('should reject null values', () => {
      expect(() => validateNonEmptyString(null as any)).toThrow('Value cannot be null');
    });

    test('should reject undefined values', () => {
      expect(() => validateNonEmptyString(undefined as any)).toThrow('Value cannot be undefined');
    });

    test('should reject empty strings', () => {
      expect(() => validateNonEmptyString('')).toThrow('String cannot be empty');
    });

    test('should reject non-string values', () => {
      expect(() => validateNonEmptyString(123 as any)).toThrow('Value must be a string');
    });
  });

  describe('validateNumberRange', () => {
    test('should accept numbers within valid range', () => {
      expect(() => validateNumberRange(5, 0, 10)).not.toThrow();
      expect(() => validateNumberRange(0, 0, 10)).not.toThrow();
      expect(() => validateNumberRange(10, 0, 10)).not.toThrow();
    });

    test('should reject null values', () => {
      expect(() => validateNumberRange(null as any, 0, 10)).toThrow('Value cannot be null');
    });

    test('should reject undefined values', () => {
      expect(() => validateNumberRange(undefined as any, 0, 10)).toThrow('Value cannot be undefined');
    });

    test('should reject numbers below minimum', () => {
      expect(() => validateNumberRange(-1, 0, 10)).toThrow('Value -1 is below minimum 0');
    });

    test('should reject numbers above maximum', () => {
      expect(() => validateNumberRange(11, 0, 10)).toThrow('Value 11 is above maximum 10');
    });

    test('should reject non-numeric values', () => {
      expect(() => validateNumberRange('5' as any, 0, 10)).toThrow('Value must be a number');
    });
  });

  describe('validateApiResponse', () => {
    test('should accept successful responses', () => {
      const mockResponse = {
        ok: true,
        status: 200,
        json: async () => ({ data: 'test' })
      };
      expect(() => validateApiResponse(mockResponse as Response)).not.toThrow();
    });

    test('should reject null responses', () => {
      expect(() => validateApiResponse(null as any)).toThrow('Response cannot be null');
    });

    test('should reject undefined responses', () => {
      expect(() => validateApiResponse(undefined as any)).toThrow('Response cannot be undefined');
    });

    test('should reject failed responses', () => {
      const mockResponse = {
        ok: false,
        status: 404,
        json: async () => ({ error: 'Not found' })
      };
      expect(() => validateApiResponse(mockResponse as Response)).toThrow('API request failed with status 404');
    });
  });
});
