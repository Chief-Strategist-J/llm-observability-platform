"use client";

import React, { useState } from "react";
import Link from "next/link";
import { Eye, EyeOff } from "lucide-react";
import { Button } from "../../../components/primitives/Button";
import { Input } from "../../../components/primitives/Input";

export interface SignUpFormProps {
  initialName?: string;
  initialOrgName?: string;
  initialEmail?: string;
  initialPassword?: string;
  loading?: boolean;
  errorMsg?: string | null;
  onSubmit: (payload: { name: string; organization_name: string; email: string; password?: string }) => void;
}

export function SignUpForm({
  initialName = "",
  initialOrgName = "",
  initialEmail = "",
  initialPassword = "",
  loading = false,
  errorMsg = null,
  onSubmit,
}: SignUpFormProps) {
  const [name, setName] = useState(initialName);
  const [orgName, setOrgName] = useState(initialOrgName);
  const [email, setEmail] = useState(initialEmail);
  const [password, setPassword] = useState(initialPassword);
  const [showPassword, setShowPassword] = useState(false);

  const getPasswordStrength = (pass: string) => {
    if (!pass) return { label: "", score: 0, color: "" };
    if (pass.length < 8) return { label: "Weak", score: 1, color: "bg-[hsl(var(--destructive))]" };
    if (pass.length < 12) return { label: "Medium", score: 2, color: "bg-amber-500" };
    return { label: "Strong", score: 3, color: "bg-emerald-500" };
  };

  const strength = getPasswordStrength(password);

  return (
    <div className="auth-card">
      <div className="auth-header">
        <h1 className="auth-title">Register Organization</h1>
        <p className="auth-subtitle">Create your multi-tenant organization workspace</p>
      </div>

      {errorMsg && <div className="auth-error-alert">{errorMsg}</div>}

      <form
        onSubmit={(e) => {
          e.preventDefault();
          onSubmit({ name, organization_name: orgName, email, password });
        }}
        className="auth-form"
      >
        <div className="auth-field">
          <label htmlFor="name" className="auth-label">
            Full Name
          </label>
          <Input
            id="name"
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="Jaydeep"
            required
          />
        </div>

        <div className="auth-field">
          <label htmlFor="orgName" className="auth-label">
            Organization Name
          </label>
          <Input
            id="orgName"
            type="text"
            value={orgName}
            onChange={(e) => setOrgName(e.target.value)}
            placeholder="Scaibu"
            required
          />
        </div>

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
            Password (Min 12 chars)
          </label>
          <div className="auth-password-wrapper">
            <Input
              id="password"
              type={showPassword ? "text" : "password"}
              value={password}
              minLength={12}
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

          {password && (
            <div className="auth-strength-meter">
              <div className="auth-strength-label">
                <span>Strength: {strength.label}</span>
              </div>
              <div className="auth-strength-track">
                <div
                  className={`auth-strength-bar ${strength.color} ${
                    strength.score === 1 ? "w-1/3" : strength.score === 2 ? "w-2/3" : "w-full"
                  }`}
                />
              </div>
            </div>
          )}
        </div>

        <Button type="submit" className="auth-submit-btn" disabled={loading}>
          {loading ? "Creating Organization..." : "Register Organization"}
        </Button>
      </form>

      <div className="auth-footer">
        Already have an organization?{" "}
        <Link href="/auth/sign-in" className="auth-footer-link">
          Sign In
        </Link>
      </div>
    </div>
  );
}
