import { safeAsyncCall, ApiError, ValidationError } from '../errorHandling';

describe('Error Handling Utilities', () => {
  describe('ApiError', () => {
    test('should create ApiError with message', () => {
      const error = new ApiError('Test error');
      expect(error.message).toBe('Test error');
      expect(error.name).toBe('ApiError');
    });

    test('should inherit from Error', () => {
      const error = new ApiError('Test error');
      expect(error instanceof Error).toBe(true);
    });
  });

  describe('ValidationError', () => {
    test('should create ValidationError with message', () => {
      const error = new ValidationError('Invalid input');
      expect(error.message).toBe('Invalid input');
      expect(error.name).toBe('ValidationError');
    });

    test('should inherit from Error', () => {
      const error = new ValidationError('Invalid input');
      expect(error instanceof Error).toBe(true);
    });
  });

  describe('safeAsyncCall', () => {
    test('should resolve with result when function succeeds', async () => {
      const successFn = async () => 'success result';
      const result = await safeAsyncCall(successFn, 'Default error', 'test-context');
      expect(result).toBe('success result');
    });

    test('should throw ApiError when function throws string', async () => {
      const errorFn = async () => {
        throw 'Network error';
      };
      await expect(safeAsyncCall(errorFn, 'Default error', 'test-context'))
        .rejects.toThrow('Default error: Network error');
    });

    test('should throw ApiError when function throws Error', async () => {
      const errorFn = async () => {
        throw new Error('Network error');
      };
      await expect(safeAsyncCall(errorFn, 'Default error', 'test-context'))
        .rejects.toThrow('Default error: Network error');
    });

    test('should throw ApiError with null error message when function throws null', async () => {
      const errorFn = async () => {
        throw null;
      };
      await expect(safeAsyncCall(errorFn, 'Default error', 'test-context'))
        .rejects.toThrow('Default error: Null error occurred');
    });

    test('should throw ApiError with undefined error message when function throws undefined', async () => {
      const errorFn = async () => {
        throw undefined;
      };
      await expect(safeAsyncCall(errorFn, 'Default error', 'test-context'))
        .rejects.toThrow('Default error: Undefined error occurred');
    });

    test('should work with functions that return promises', async () => {
      const successFn = () => Promise.resolve('promise result');
      const result = await safeAsyncCall(successFn, 'Default error', 'test-context');
      expect(result).toBe('promise result');
    });

    test('should work with functions that return rejected promises', async () => {
      const errorFn = () => Promise.reject('Promise rejected');
      await expect(safeAsyncCall(errorFn, 'Default error', 'test-context'))
        .rejects.toThrow('Default error: Promise rejected');
    });
  });
});
