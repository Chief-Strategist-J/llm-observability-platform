"use client";

import React, { useState } from "react";
import Link from "next/link";
import { Eye, EyeOff } from "lucide-react";
import { Button } from "../../../components/primitives/Button";
import { Input } from "../../../components/primitives/Input";

export interface SignInFormProps {
  initialEmail?: string;
  initialPassword?: string;
  loading?: boolean;
  errorMsg?: string | null;
  onSubmit: (payload: { email: string; password?: string }) => void;
}

export function SignInForm({
  initialEmail = "",
  initialPassword = "",
  loading = false,
  errorMsg = null,
  onSubmit,
}: SignInFormProps) {
  const [email, setEmail] = useState(initialEmail);
  const [password, setPassword] = useState(initialPassword);
  const [showPassword, setShowPassword] = useState(false);

  return (
    <div className="auth-card">
      <div className="auth-header">
        <h1 className="auth-title">Sign In</h1>
        <p className="auth-subtitle">Sign in to access your multi-tenant observability workspace</p>
      </div>

      {errorMsg && <div className="auth-error-alert">{errorMsg}</div>}

      <form
        onSubmit={(e) => {
          e.preventDefault();
          onSubmit({ email, password });
        }}
        className="auth-form"
      >
        <div className="auth-field">
          <label htmlFor="email" className="auth-label">
            Email Address
          </label>
          <Input
            id="email"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="jaydeep@gmail.com"
            required
          />
        </div>

        <div className="auth-field">
          <label htmlFor="password" className="auth-label">
            Password
          </label>
          <div className="auth-password-wrapper">
            <Input
              id="password"
              type={showPassword ? "text" : "password"}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••••••"
              className="pr-10"
              required
            />
            <button
              type="button"
              aria-label={showPassword ? "Hide password" : "Show password"}
              onClick={() => setShowPassword(!showPassword)}
              className="auth-password-toggle"
            >
              {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
            </button>
          </div>
        </div>

        <Button type="submit" className="auth-submit-btn" disabled={loading}>
          {loading ? "Authenticating..." : "Sign In to Workspace"}
        </Button>
      </form>

      <div className="auth-footer">
        Need a new organization?{" "}
        <Link href="/auth/sign-up" className="auth-footer-link">
          Register Organization
        </Link>
      </div>
    </div>
  );
}
