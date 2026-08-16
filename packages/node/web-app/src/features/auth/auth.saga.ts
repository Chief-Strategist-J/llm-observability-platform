import { call, put, takeEvery } from "redux-saga/effects";
import { authActions } from "./auth.slice";
import { authApiClient } from "../../lib/auth-client";
import { eventBus } from "../../core/event-bus/event-bus";
import { AUTH_MESSAGES, AUTH_EVENTS, AUTH_ROLES } from "./auth.constants";

function getCookieToken(): string | undefined {
  if (typeof document === "undefined") return undefined;
  const match = document.cookie.match(new RegExp("(?:^|; )authjs\\.session-token=([^;]*)"));
  return match ? decodeURIComponent(match[1]) : undefined;
}

function setAuthCookies(token: string, role?: string) {
  if (typeof document !== "undefined") {
    document.cookie = `authjs.session-token=${token}; path=/`;
    document.cookie = `user_role=${role || AUTH_ROLES.OWNER}; path=/`;
  }
}

function clearAuthCookies() {
  if (typeof document !== "undefined") {
    document.cookie = "authjs.session-token=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT";
    document.cookie = "user_role=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT";
  }
}

function* handleSignUp(action: ReturnType<typeof authActions.signUpSubmitted>): Generator<any, void, any> {
  try {
    const response = yield call([authApiClient, "signUp"], action.payload);
    yield put(authActions.authSuccess({ user: response.user, organization: response.user ? { id: response.user.org_id, name: response.user.org_name } : null }));
    if (response.token) {
      setAuthCookies(response.token, response.user?.role);
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
    yield put(authActions.authSuccess({ user: response.user, organization: response.user ? { id: response.user.org_id, name: response.user.org_name } : null }));
    if (response.token) {
      setAuthCookies(response.token, response.user?.role);
    }
    eventBus.emit(AUTH_EVENTS.SIGN_IN_SUCCESS, response);
  } catch (err: any) {
    const errorMsg = err?.message || AUTH_MESSAGES.SIGN_IN_FAILED;
    yield put(authActions.authFailed(errorMsg));
    eventBus.emit(AUTH_EVENTS.SIGN_IN_FAILURE, errorMsg);
  }
}

function* handleSignOut(): Generator<any, void, any> {
  try {
    const token = getCookieToken();
    if (token) {
      yield call([authApiClient, "signOut"], token);
    }
    clearAuthCookies();
    yield put(authActions.loggedOut());
    eventBus.emit(AUTH_EVENTS.SIGN_OUT_SUCCESS, null);
  } catch (err: any) {
    clearAuthCookies();
    yield put(authActions.loggedOut());
    eventBus.emit(AUTH_EVENTS.SIGN_OUT_SUCCESS, null);
  }
}

function* handleFetchOrganizations(): Generator<any, void, any> {
  try {
    const token = getCookieToken();
    const orgs = yield call([authApiClient, "listOrganizations"], token);
    yield put(authActions.setOrganizations(orgs || []));
  } catch (err: any) {
    console.error("Failed to fetch organizations:", err);
  }
}

function* handleSwitchOrganization(action: ReturnType<typeof authActions.switchOrganizationSubmitted>): Generator<any, void, any> {
  try {
    const token = getCookieToken();
    const result = yield call([authApiClient, "switchOrganization"], action.payload.orgId, token);
    if (result.token) {
      setAuthCookies(result.token, result.payload?.org?.role);
    }
    yield put(authActions.authSuccess({
      user: { id: result.payload.sub, email: result.payload.email, org_id: result.payload.org.org_id, org_name: result.payload.org.org_name, role: result.payload.org.role },
      organization: { id: result.payload.org.org_id, name: result.payload.org.org_name },
    }));
    eventBus.emit(AUTH_EVENTS.ORG_SWITCH_SUCCESS, result);
  } catch (err: any) {
    const errorMsg = err?.message || AUTH_MESSAGES.ORG_SWITCH_FAILED;
    yield put(authActions.authFailed(errorMsg));
    eventBus.emit(AUTH_EVENTS.ORG_SWITCH_FAILURE, errorMsg);
  }
}

function* handleFetchMembers(): Generator<any, void, any> {
  try {
    const token = getCookieToken();
    const members = yield call([authApiClient, "listUsers"], token);
    yield put(authActions.setMembers(members || []));
  } catch (err: any) {
    console.error("Failed to fetch members:", err);
  }
}

function* handleInviteUser(action: ReturnType<typeof authActions.inviteUserSubmitted>): Generator<any, void, any> {
  try {
    const token = getCookieToken();
    const invited = yield call([authApiClient, "inviteUser"], action.payload, token);
    yield put(authActions.fetchMembersSubmitted());
    eventBus.emit(AUTH_EVENTS.INVITE_SUCCESS, invited);
  } catch (err: any) {
    const errorMsg = err?.message || AUTH_MESSAGES.INVITE_FAILED;
    yield put(authActions.authFailed(errorMsg));
    eventBus.emit(AUTH_EVENTS.INVITE_FAILURE, errorMsg);
  }
}

function* handleFetchApiKeys(): Generator<any, void, any> {
  try {
    const token = getCookieToken();
    const keys = yield call([authApiClient, "listApiKeys"], token);
    yield put(authActions.setApiKeys(keys || []));
  } catch (err: any) {
    console.error("Failed to fetch API keys:", err);
  }
}

function* handleFetchAuditLogs(action: ReturnType<typeof authActions.fetchAuditLogsSubmitted>): Generator<any, void, any> {
  try {
    const token = getCookieToken();
    const logs = yield call([authApiClient, "fetchAuditLogs"], action.payload, token);
    yield put(authActions.setAuditLogs(logs || []));
  } catch (err: any) {
    console.error("Failed to fetch audit logs:", err);
  }
}

export function* authSaga() {
  yield takeEvery(authActions.signUpSubmitted.type, handleSignUp);
  yield takeEvery(authActions.signInSubmitted.type, handleSignIn);
  yield takeEvery(authActions.signOutSubmitted.type, handleSignOut);
  yield takeEvery(authActions.fetchOrganizationsSubmitted.type, handleFetchOrganizations);
  yield takeEvery(authActions.switchOrganizationSubmitted.type, handleSwitchOrganization);
  yield takeEvery(authActions.fetchMembersSubmitted.type, handleFetchMembers);
  yield takeEvery(authActions.inviteUserSubmitted.type, handleInviteUser);
  yield takeEvery(authActions.fetchApiKeysSubmitted.type, handleFetchApiKeys);
  yield takeEvery(authActions.fetchAuditLogsSubmitted.type, handleFetchAuditLogs);
}
