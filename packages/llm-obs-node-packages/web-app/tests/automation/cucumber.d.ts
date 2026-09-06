declare module '@cucumber/cucumber' {
  export function Given(pattern: string | RegExp, fn: Function): void;
  export function When(pattern: string | RegExp, fn: Function): void;
  export function Then(pattern: string | RegExp, fn: Function): void;
  export function Before(fn: Function): void;
  export function After(fn: Function): void;
  export function BeforeAll(fn: Function): void;
  export function AfterAll(fn: Function): void;

  export enum Status {
    PASSED = 'PASSED',
    FAILED = 'FAILED',
    SKIPPED = 'SKIPPED',
    PENDING = 'PENDING',
    UNDEFINED = 'UNDEFINED',
    AMBIGUOUS = 'AMBIGUOUS',
  }

  export interface ITestCaseHookParameter {
    result?: {
      status?: Status;
      duration?: number;
      message?: string;
    };
    pickle?: {
      id?: string;
      name?: string;
    };
  }
}
