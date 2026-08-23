import { RequestContext } from '@observability/core';

export interface BaseCommand {
  context?: Partial<RequestContext>;
}

export interface SignUpUserCommand extends BaseCommand {
  type: 'SIGN_UP_USER';
  payload: {
    userId: string;
    email: string;
    orgId: string;
  };
}

export interface SignInUserCommand extends BaseCommand {
  type: 'SIGN_IN_USER';
  payload: {
    userId: string;
    email: string;
    orgId: string;
  };
}

export type AuthCommand = SignUpUserCommand | SignInUserCommand;
