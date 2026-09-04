/**
 * Authentication feature constants, route paths, cookie definitions, messages, and events.
 */

export const AUTH_DEFAULT_FIXTURES = {
  NAME: "Jaydeep",
  ORG_NAME: "Scaibu",
  EMAIL: "jaydeep@gmail.com",
  PASSWORD: "Password12345!",
} as const;

export const AUTH_ROUTES = {
  SIGN_IN: "/auth/sign-in",
  SIGN_UP: "/auth/sign-up",
  DASHBOARD: "/",
} as const;

export const AUTH_COOKIE_KEYS = {
  SESSION_TOKEN: "authjs.session-token",
  USER_ROLE: "user_role",
  DEFAULT_PATH: "path=/",
  EXPIRED_DATE: "Thu, 01 Jan 1970 00:00:00 GMT",
} as const;

export const AUTH_MESSAGES = {
  SIGN_UP_FAILED: "Sign up failed. Please try again.",
  SIGN_IN_FAILED: "Sign in failed. Invalid credentials.",
  SIGN_OUT_FAILED: "Sign out failed.",
  ORG_SWITCH_FAILED: "Failed to switch organization context.",
  INVITE_FAILED: "Failed to invite user.",
  FETCH_ORGS_FAILED: "Failed to fetch organization list.",
  FETCH_MEMBERS_FAILED: "Failed to fetch organization members.",
  FETCH_API_KEYS_FAILED: "Failed to fetch organization API keys.",
  FETCH_AUDIT_LOGS_FAILED: "Failed to fetch organization audit logs.",
  USER_BLOCKED: "Access Denied: Your user account has been blocked by your organization administrator.",
  UNEXPECTED_ERROR: "An unexpected error occurred",
} as const;

export const AUTH_ROLES = {
  ADMIN: "admin",
  MEMBER: "member",
  VIEWER: "viewer",
  OWNER: "owner",
} as const;

export const AUTH_EVENTS = {
  SIGN_UP_SUCCESS: "auth.signUpSuccess",
  SIGN_UP_FAILURE: "auth.signUpFailure",
  SIGN_IN_SUCCESS: "auth.signInSuccess",
  SIGN_IN_FAILURE: "auth.signInFailure",
  SIGN_OUT_SUCCESS: "auth.signOutSuccess",
  SIGN_OUT_FAILURE: "auth.signOutFailure",
  ORG_SWITCH_SUCCESS: "auth.orgSwitchSuccess",
  ORG_SWITCH_FAILURE: "auth.orgSwitchFailure",
  INVITE_SUCCESS: "auth.inviteSuccess",
  INVITE_FAILURE: "auth.inviteFailure",
  UNAUTHORIZED: "auth.unauthorized",
} as const;
