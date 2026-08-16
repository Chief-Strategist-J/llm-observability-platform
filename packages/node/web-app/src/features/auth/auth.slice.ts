import { createSlice, type PayloadAction } from "@reduxjs/toolkit";

export interface AuthState {
  status: "idle" | "loading" | "success" | "error";
  user: any | null;
  organization: any | null;
  userOrganizations: Array<{ id: string; name: string; slug: string }>;
  members: any[];
  apiKeys: any[];
  auditLogs: any[];
  error: string | null;
}

const initialState: AuthState = {
  status: "idle",
  user: null,
  organization: null,
  userOrganizations: [],
  members: [],
  apiKeys: [],
  auditLogs: [],
  error: null,
};

export const authSlice = createSlice({
  name: "auth",
  initialState,
  reducers: {
    signUpSubmitted(
      state,
      _action: PayloadAction<{ name: string; organization_name: string; email: string; password?: string }>
    ) {
      state.status = "loading";
      state.error = null;
    },
    signInSubmitted(state, _action: PayloadAction<{ email: string; password?: string }>) {
      state.status = "loading";
      state.error = null;
    },
    signOutSubmitted(state) {
      state.status = "loading";
      state.error = null;
    },
    fetchOrganizationsSubmitted(state) {
      state.error = null;
    },
    switchOrganizationSubmitted(state, _action: PayloadAction<{ orgId: string }>) {
      state.status = "loading";
      state.error = null;
    },
    fetchMembersSubmitted(state) {
      state.error = null;
    },
    inviteUserSubmitted(state, _action: PayloadAction<{ email: string; name: string; role?: string; permissions?: string[] }>) {
      state.status = "loading";
      state.error = null;
    },
    fetchApiKeysSubmitted(state) {
      state.error = null;
    },
    fetchAuditLogsSubmitted(state, _action: PayloadAction<{ event_type?: string } | undefined>) {
      state.error = null;
    },
    authSuccess(state, action: PayloadAction<{ user: any; organization?: any }>) {
      state.status = "success";
      state.user = action.payload.user;
      if (action.payload.organization) {
        state.organization = action.payload.organization;
      }
      state.error = null;
    },
    authFailed(state, action: PayloadAction<string>) {
      state.status = "error";
      state.error = action.payload;
    },
    setOrganizations(state, action: PayloadAction<Array<{ id: string; name: string; slug: string }>>) {
      state.userOrganizations = action.payload;
    },
    setMembers(state, action: PayloadAction<any[]>) {
      state.members = action.payload;
    },
    setApiKeys(state, action: PayloadAction<any[]>) {
      state.apiKeys = action.payload;
    },
    setAuditLogs(state, action: PayloadAction<any[]>) {
      state.auditLogs = action.payload;
    },
    loggedOut(state) {
      state.status = "idle";
      state.user = null;
      state.organization = null;
      state.userOrganizations = [];
      state.members = [];
      state.apiKeys = [];
      state.auditLogs = [];
      state.error = null;
    },
    resetAuthStatus(state) {
      state.status = "idle";
      state.error = null;
    },
  },
});

export const authActions = authSlice.actions;
export const authReducer = authSlice.reducer;
