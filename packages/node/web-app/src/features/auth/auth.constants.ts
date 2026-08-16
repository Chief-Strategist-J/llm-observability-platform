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

export const AUTH_MESSAGES = {
  SIGN_UP_FAILED: "Sign up failed. Please try again.",
  SIGN_IN_FAILED: "Sign in failed. Invalid credentials.",
  SIGN_OUT_FAILED: "Sign out failed.",
  ORG_SWITCH_FAILED: "Failed to switch organization context.",
  INVITE_FAILED: "Failed to invite user.",
  USER_BLOCKED: "Access Denied: Your user account has been blocked by your organization administrator.",
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
} as const;
