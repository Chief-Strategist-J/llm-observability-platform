import { RULES_ENGINE_CONSTANTS } from './constants';

export interface ErrorDescriptor {
  code: string;
  message: string;
  category: typeof RULES_ENGINE_CONSTANTS.CAT_VALIDATION | typeof RULES_ENGINE_CONSTANTS.CAT_NETWORK | typeof RULES_ENGINE_CONSTANTS.CAT_CIRCUIT_BREAKER | typeof RULES_ENGINE_CONSTANTS.CAT_RULE_BREACH | typeof RULES_ENGINE_CONSTANTS.CAT_INTERNAL;
  severity: typeof RULES_ENGINE_CONSTANTS.SEV_INFO | typeof RULES_ENGINE_CONSTANTS.SEV_WARNING | typeof RULES_ENGINE_CONSTANTS.SEV_ERROR | typeof RULES_ENGINE_CONSTANTS.SEV_CRITICAL;
  httpStatus: number;
}

class CentralizedErrorRegistry {
  private readonly errorsMap = new Map<string, ErrorDescriptor>();

  constructor() {
    this.registerDefaults();
  }

  public register(desc: ErrorDescriptor): void {
    this.errorsMap.set(desc.code, desc);
  }

  public get(code: string): ErrorDescriptor {
    return (
      this.errorsMap.get(code) || {
        code: RULES_ENGINE_CONSTANTS.ERR_UNKNOWN,
        message: RULES_ENGINE_CONSTANTS.MSG_UNKNOWN_ERROR,
        category: RULES_ENGINE_CONSTANTS.CAT_INTERNAL,
        severity: RULES_ENGINE_CONSTANTS.SEV_ERROR,
        httpStatus: 500,
      }
    );
  }

  public getAll(): ErrorDescriptor[] {
    return Array.from(this.errorsMap.values());
  }

  private registerDefaults(): void {
    this.register({
      code: RULES_ENGINE_CONSTANTS.ERR_VALIDATION_FAILED,
      message: RULES_ENGINE_CONSTANTS.MSG_VALIDATION_FAILED,
      category: RULES_ENGINE_CONSTANTS.CAT_VALIDATION,
      severity: RULES_ENGINE_CONSTANTS.SEV_WARNING,
      httpStatus: 400,
    });
    this.register({
      code: RULES_ENGINE_CONSTANTS.ERR_CIRCUIT_OPEN,
      message: RULES_ENGINE_CONSTANTS.MSG_CIRCUIT_OPEN,
      category: RULES_ENGINE_CONSTANTS.CAT_CIRCUIT_BREAKER,
      severity: RULES_ENGINE_CONSTANTS.SEV_ERROR,
      httpStatus: 503,
    });
    this.register({
      code: RULES_ENGINE_CONSTANTS.ERR_HTTP_FAILED,
      message: RULES_ENGINE_CONSTANTS.MSG_HTTP_FAILED,
      category: RULES_ENGINE_CONSTANTS.CAT_NETWORK,
      severity: RULES_ENGINE_CONSTANTS.SEV_ERROR,
      httpStatus: 502,
    });
    this.register({
      code: RULES_ENGINE_CONSTANTS.ERR_RULE_DENIED,
      message: RULES_ENGINE_CONSTANTS.MSG_RULE_DENIED,
      category: RULES_ENGINE_CONSTANTS.CAT_RULE_BREACH,
      severity: RULES_ENGINE_CONSTANTS.SEV_WARNING,
      httpStatus: 422,
    });
  }
}

export const errorRegistry = new CentralizedErrorRegistry();
