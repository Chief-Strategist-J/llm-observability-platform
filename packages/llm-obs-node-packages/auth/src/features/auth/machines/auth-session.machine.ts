export type SessionState = 'unauthenticated' | 'authenticating' | 'active_session' | 'expired' | 'revoked';
export type SessionEvent = 'SUBMIT_CREDENTIALS' | 'AUTHENTICATION_SUCCESS' | 'AUTHENTICATION_FAILURE' | 'EXPIRE' | 'REVOKE';

export interface SessionStateNode {
  on: Partial<Record<SessionEvent, SessionState>>;
}

export const AUTH_SESSION_STATE_MACHINE: Record<SessionState, SessionStateNode> = {
  unauthenticated: {
    on: {
      SUBMIT_CREDENTIALS: 'authenticating',
    },
  },
  authenticating: {
    on: {
      AUTHENTICATION_SUCCESS: 'active_session',
      AUTHENTICATION_FAILURE: 'unauthenticated',
    },
  },
  active_session: {
    on: {
      EXPIRE: 'expired',
      REVOKE: 'revoked',
    },
  },
  expired: {
    on: {
      SUBMIT_CREDENTIALS: 'authenticating',
    },
  },
  revoked: {
    on: {
      SUBMIT_CREDENTIALS: 'authenticating',
    },
  },
};

export function transitionSessionState(currentState: SessionState, event: SessionEvent): SessionState {
  const node = AUTH_SESSION_STATE_MACHINE[currentState];
  const nextState = node.on[event];
  if (!nextState) {
    throw new Error(`Invalid session state transition: ${currentState} -> ${event}`);
  }
  return nextState;
}
