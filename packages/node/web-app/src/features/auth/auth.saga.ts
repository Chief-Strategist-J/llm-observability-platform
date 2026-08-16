import { call, put, takeEvery } from "redux-saga/effects";
import { authActions } from "./auth.slice";
import { authApiClient } from "../../lib/auth-client";
import { eventBus } from "../../core/event-bus/event-bus";
import { AUTH_MESSAGES, AUTH_EVENTS, AUTH_ROLES } from "./auth.constants";

function* handleSignUp(action: ReturnType<typeof authActions.signUpSubmitted>): Generator<any, void, any> {
  try {
    const response = yield call([authApiClient, "signUp"], action.payload);
    yield put(authActions.authSuccess({ user: response.user, organization: response.organization }));
    if (typeof document !== "undefined") {
      document.cookie = `authjs.session-token=mock-token-${response.user?.id || "123"}; path=/`;
      document.cookie = `user_role=${response.user?.role || AUTH_ROLES.OWNER}; path=/`;
    }
    eventBus.emit(AUTH_EVENTS.SIGN_UP_SUCCESS, response);
  } catch (err: any) {
    const errorMsg = err?.message || AUTH_MESSAGES.SIGN_UP_FAILED;
    yield put(authActions.authFailed(errorMsg));
    eventBus.emit(AUTH_EVENTS.SIGN_UP_FAILURE, errorMsg);
  }
}

function* handleSignIn(action: ReturnType<typeof authActions.signInSubmitted>): Generator<any, void, any> {
  try {
    const response = yield call([authApiClient, "signIn"], action.payload);
    yield put(authActions.authSuccess({ user: response.user }));
    if (typeof document !== "undefined") {
      document.cookie = `authjs.session-token=${response.token}; path=/`;
      document.cookie = `user_role=${response.user?.role || AUTH_ROLES.OWNER}; path=/`;
    }
    eventBus.emit(AUTH_EVENTS.SIGN_IN_SUCCESS, response);
  } catch (err: any) {
    const errorMsg = err?.message || AUTH_MESSAGES.SIGN_IN_FAILED;
    yield put(authActions.authFailed(errorMsg));
    eventBus.emit(AUTH_EVENTS.SIGN_IN_FAILURE, errorMsg);
  }
}

export function* authSaga() {
  yield takeEvery(authActions.signUpSubmitted.type, handleSignUp);
  yield takeEvery(authActions.signInSubmitted.type, handleSignIn);
}
