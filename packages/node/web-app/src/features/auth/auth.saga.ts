import { call, put, takeEvery } from "redux-saga/effects";
import { authActions } from "./auth.slice";
import { authApiClient } from "../../lib/auth-client";
import { eventBus } from "../../core/event-bus/event-bus";

function* handleSignUp(action: ReturnType<typeof authActions.signUpSubmitted>): Generator<any, void, any> {
  try {
    const response = yield call([authApiClient, "signUp"], action.payload);
    yield put(authActions.authSuccess({ user: response.user, organization: response.organization }));
    if (typeof document !== "undefined") {
      document.cookie = `authjs.session-token=mock-token-${response.user?.id || "123"}; path=/`;
      document.cookie = `mock_role=${response.user?.role || "owner"}; path=/`;
    }
    eventBus.emit("auth.signUpSuccess", response);
  } catch (err: any) {
    const errorMsg = err?.message || "Sign up failed. Please try again.";
    yield put(authActions.authFailed(errorMsg));
    eventBus.emit("auth.signUpFailure", errorMsg);
  }
}

function* handleSignIn(action: ReturnType<typeof authActions.signInSubmitted>): Generator<any, void, any> {
  try {
    const response = yield call([authApiClient, "signIn"], action.payload);
    yield put(authActions.authSuccess({ user: response.user }));
    if (typeof document !== "undefined") {
      document.cookie = `authjs.session-token=${response.token}; path=/`;
      document.cookie = `mock_role=${response.user?.role || "owner"}; path=/`;
    }
    eventBus.emit("auth.signInSuccess", response);
  } catch (err: any) {
    const errorMsg = err?.message || "Sign in failed. Invalid credentials.";
    yield put(authActions.authFailed(errorMsg));
    eventBus.emit("auth.signInFailure", errorMsg);
  }
}

export function* authSaga() {
  yield takeEvery(authActions.signUpSubmitted.type, handleSignUp);
  yield takeEvery(authActions.signInSubmitted.type, handleSignIn);
}
