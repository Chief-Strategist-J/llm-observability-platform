/**
 * Centralized Saga error handling and session management wrapper.
 */

import { call, put } from "redux-saga/effects";
import { isUnauthorizedError, compareNormalized } from "../utils/string-utils";
import { eventBus } from "../event-bus/event-bus";
import { authActions } from "../../features/auth/auth.slice";
import { AUTH_COOKIE_KEYS, AUTH_EVENTS, AUTH_MESSAGES } from "../../features/auth/auth.constants";

function clearAuthCookies() {
  if (!compareNormalized(typeof document, "undefined")) {
    document.cookie = `${AUTH_COOKIE_KEYS.SESSION_TOKEN}=; ${AUTH_COOKIE_KEYS.DEFAULT_PATH}; expires=${AUTH_COOKIE_KEYS.EXPIRED_DATE}`;
    document.cookie = `${AUTH_COOKIE_KEYS.USER_ROLE}=; ${AUTH_COOKIE_KEYS.DEFAULT_PATH}; expires=${AUTH_COOKIE_KEYS.EXPIRED_DATE}`;
  }
}

export function safeSaga<T extends (...args: any[]) => Generator<any, void, any>>(
  sagaFn: T,
  config?: {
    fallbackError?: string;
    failureAction?: (errorMsg: string) => any;
    failureEvent?: string;
  }
) {
  return function* (...args: Parameters<T>): Generator<any, void, any> {
    try {
      yield call(sagaFn, ...args);
    } catch (err: any) {
      if (isUnauthorizedError(err)) {
        clearAuthCookies();
        yield put(authActions.loggedOut());
        eventBus.emit(AUTH_EVENTS.UNAUTHORIZED, { error: err });
      }

      const errorMsg = err?.message || config?.fallbackError || AUTH_MESSAGES.UNEXPECTED_ERROR;

      if (config?.failureAction) {
        yield put(config.failureAction(errorMsg));
      }
      if (config?.failureEvent) {
        eventBus.emit(config.failureEvent, typeof config.failureEvent === "string" ? { error: errorMsg } : errorMsg);
      }
    }
  };
}
