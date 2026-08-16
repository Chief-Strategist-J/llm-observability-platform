import { createSlice, type PayloadAction } from "@reduxjs/toolkit";

export interface AuthState {
  status: "idle" | "loading" | "success" | "error";
  user: any | null;
  organization: any | null;
  error: string | null;
}

const initialState: AuthState = {
  status: "idle",
  user: null,
  organization: null,
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
    authSuccess(state, action: PayloadAction<{ user: any; organization?: any }>) {
      state.status = "success";
      state.user = action.payload.user;
      state.organization = action.payload.organization || null;
      state.error = null;
    },
    authFailed(state, action: PayloadAction<string>) {
      state.status = "error";
      state.error = action.payload;
    },
    resetAuthStatus(state) {
      state.status = "idle";
      state.error = null;
    },
  },
});

export const authActions = authSlice.actions;
export const authReducer = authSlice.reducer;
