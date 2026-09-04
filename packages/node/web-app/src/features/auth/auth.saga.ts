/**
 * Authentication Redux Saga handling sign up, sign in, sign out, organization switching, and member management.
 */

import { call, put, takeEvery } from "redux-saga/effects";
import { authActions } from "./auth.slice";
import { authApiClient } from "../../lib/api/auth-client";
import { eventBus } from "../../core/event-bus/event-bus";
import { AUTH_MESSAGES, AUTH_EVENTS, AUTH_ROLES, AUTH_COOKIE_KEYS } from "./auth.constants";
import { safeSaga } from "../../core/store/saga-wrapper";
import { compareNormalized } from "../../core/utils/string-utils";

function getCookieToken(): string | undefined {
  if (compareNormalized(typeof document, "undefined")) return undefined;
  const regex = new RegExp(`(?:^|; )${AUTH_COOKIE_KEYS.SESSION_TOKEN.replace(".", "\\.")}=([^;]*)`);
  const match = document.cookie.match(regex);
  return match && match[1] ? decodeURIComponent(match[1]) : undefined;
}

function setAuthCookies(token: string, role?: string) {
  if (!compareNormalized(typeof document, "undefined")) {
    document.cookie = `${AUTH_COOKIE_KEYS.SESSION_TOKEN}=${token}; ${AUTH_COOKIE_KEYS.DEFAULT_PATH}`;
    document.cookie = `${AUTH_COOKIE_KEYS.USER_ROLE}=${role || AUTH_ROLES.OWNER}; ${AUTH_COOKIE_KEYS.DEFAULT_PATH}`;
  }
}

function clearAuthCookies() {
  if (!compareNormalized(typeof document, "undefined")) {
    document.cookie = `${AUTH_COOKIE_KEYS.SESSION_TOKEN}=; ${AUTH_COOKIE_KEYS.DEFAULT_PATH}; expires=${AUTH_COOKIE_KEYS.EXPIRED_DATE}`;
    document.cookie = `${AUTH_COOKIE_KEYS.USER_ROLE}=; ${AUTH_COOKIE_KEYS.DEFAULT_PATH}; expires=${AUTH_COOKIE_KEYS.EXPIRED_DATE}`;
  }
}

function* handleSignUp(action: ReturnType<typeof authActions.signUpSubmitted>): Generator<any, void, any> {
  const response = yield call(() => authApiClient.signUp(action.payload));
  yield put(authActions.authSuccess({ user: response.user, organization: response.user ? { id: response.user.org_id, name: response.user.org_name } : null }));
  if (response.token) {
    setAuthCookies(response.token, response.user?.role);
  }
  eventBus.emit(AUTH_EVENTS.SIGN_UP_SUCCESS, response);
}

function* handleSignIn(action: ReturnType<typeof authActions.signInSubmitted>): Generator<any, void, any> {
  const response = yield call(() => authApiClient.signIn(action.payload));
  yield put(authActions.authSuccess({ user: response.user, organization: response.user ? { id: response.user.org_id, name: response.user.org_name } : null }));
  if (response.token) {
    setAuthCookies(response.token, response.user?.role);
  }
  eventBus.emit(AUTH_EVENTS.SIGN_IN_SUCCESS, response);
}

function* handleSignOut(): Generator<any, void, any> {
  const token = getCookieToken();
  if (token) {
    yield call(() => authApiClient.signOut(token));
  }
  clearAuthCookies();
  yield put(authActions.loggedOut());
  eventBus.emit(AUTH_EVENTS.SIGN_OUT_SUCCESS, null);
}

function* handleFetchOrganizations(): Generator<any, void, any> {
  const token = getCookieToken();
  const orgs = yield call(() => authApiClient.listOrganizations(token));
  yield put(authActions.setOrganizations(orgs || []));
}

function* handleSwitchOrganization(action: ReturnType<typeof authActions.switchOrganizationSubmitted>): Generator<any, void, any> {
  const token = getCookieToken();
  const result = yield call(() => authApiClient.switchOrganization(action.payload.orgId, token));
  if (result.token) {
    setAuthCookies(result.token, result.payload?.org?.role);
  }
  yield put(authActions.authSuccess({
    user: { id: result.payload.sub, email: result.payload.email, org_id: result.payload.org.org_id, org_name: result.payload.org.org_name, role: result.payload.org.role },
    organization: { id: result.payload.org.org_id, name: result.payload.org.org_name },
  }));
  eventBus.emit(AUTH_EVENTS.ORG_SWITCH_SUCCESS, result);
}

function* handleFetchMembers(): Generator<any, void, any> {
  const token = getCookieToken();
  const members = yield call(() => authApiClient.listUsers(token));
  yield put(authActions.setMembers(members || []));
}

function* handleInviteUser(action: ReturnType<typeof authActions.inviteUserSubmitted>): Generator<any, void, any> {
  const token = getCookieToken();
  const invited = yield call(() => authApiClient.inviteUser(action.payload, token));
  yield put(authActions.fetchMembersSubmitted());
  eventBus.emit(AUTH_EVENTS.INVITE_SUCCESS, invited);
}

function* handleFetchApiKeys(): Generator<any, void, any> {
  const token = getCookieToken();
  const keys = yield call(() => authApiClient.listApiKeys(token));
  yield put(authActions.setApiKeys(keys || []));
}

function* handleFetchAuditLogs(action: ReturnType<typeof authActions.fetchAuditLogsSubmitted>): Generator<any, void, any> {
  const token = getCookieToken();
  const logs = yield call(() => authApiClient.fetchAuditLogs(action.payload, token));
  yield put(authActions.setAuditLogs(logs || []));
}

export function* authSaga() {
  yield takeEvery(
    authActions.signUpSubmitted.type,
    safeSaga(handleSignUp, { failureAction: authActions.authFailed, failureEvent: AUTH_EVENTS.SIGN_UP_FAILURE, fallbackError: AUTH_MESSAGES.SIGN_UP_FAILED })
  );
  yield takeEvery(
    authActions.signInSubmitted.type,
    safeSaga(handleSignIn, { failureAction: authActions.authFailed, failureEvent: AUTH_EVENTS.SIGN_IN_FAILURE, fallbackError: AUTH_MESSAGES.SIGN_IN_FAILED })
  );
  yield takeEvery(
    authActions.signOutSubmitted.type,
    safeSaga(handleSignOut, { failureEvent: AUTH_EVENTS.SIGN_OUT_SUCCESS, fallbackError: AUTH_MESSAGES.SIGN_OUT_FAILED })
  );
  yield takeEvery(
    authActions.fetchOrganizationsSubmitted.type,
    safeSaga(handleFetchOrganizations, { failureAction: authActions.authFailed, fallbackError: AUTH_MESSAGES.FETCH_ORGS_FAILED })
  );
  yield takeEvery(
    authActions.switchOrganizationSubmitted.type,
    safeSaga(handleSwitchOrganization, { failureAction: authActions.authFailed, failureEvent: AUTH_EVENTS.ORG_SWITCH_FAILURE, fallbackError: AUTH_MESSAGES.ORG_SWITCH_FAILED })
  );
  yield takeEvery(
    authActions.fetchMembersSubmitted.type,
    safeSaga(handleFetchMembers, { failureAction: authActions.authFailed, fallbackError: AUTH_MESSAGES.FETCH_MEMBERS_FAILED })
  );
  yield takeEvery(
    authActions.inviteUserSubmitted.type,
    safeSaga(handleInviteUser, { failureAction: authActions.authFailed, failureEvent: AUTH_EVENTS.INVITE_FAILURE, fallbackError: AUTH_MESSAGES.INVITE_FAILED })
  );
  yield takeEvery(
    authActions.fetchApiKeysSubmitted.type,
    safeSaga(handleFetchApiKeys, { failureAction: authActions.authFailed, fallbackError: AUTH_MESSAGES.FETCH_API_KEYS_FAILED })
  );
  yield takeEvery(
    authActions.fetchAuditLogsSubmitted.type,
    safeSaga(handleFetchAuditLogs, { failureAction: authActions.authFailed, fallbackError: AUTH_MESSAGES.FETCH_AUDIT_LOGS_FAILED })
  );
}
