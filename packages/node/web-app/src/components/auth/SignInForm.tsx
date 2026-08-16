"use client";

import React, { useState } from "react";
import Link from "next/link";
import { Eye, EyeOff } from "lucide-react";
import { Button } from "../primitives/Button";
import { Input } from "../primitives/Input";

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
    <div className="w-full max-w-md rounded-[var(--radius-xl)] border border-[hsl(var(--border))] bg-[hsl(var(--card))] p-8 shadow-lg space-y-6 text-left">
      <div className="text-left space-y-1.5 mb-6">
        <h1 className="text-2xl font-bold tracking-tight text-[hsl(var(--foreground))] text-left">
          Sign In
        </h1>
        <p className="text-xs text-[hsl(var(--muted-foreground))] text-left">
          Sign in to access your multi-tenant observability workspace
        </p>
      </div>

      {errorMsg && (
        <div className="rounded-[var(--radius-md)] border border-[hsl(var(--destructive)/.4)] bg-[hsl(var(--destructive)/.15)] p-3.5 text-xs text-[hsl(var(--destructive))] font-medium text-left">
          {errorMsg}
        </div>
      )}

      <form
        onSubmit={(e) => {
          e.preventDefault();
          onSubmit({ email, password });
        }}
        className="space-y-4 text-left"
      >
        <div className="flex flex-col gap-1.5 text-left">
          <label htmlFor="email" className="text-xs font-semibold uppercase text-[hsl(var(--muted-foreground))] text-left">
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

        <div className="flex flex-col gap-1.5 text-left">
          <label htmlFor="password" className="text-xs font-semibold uppercase text-[hsl(var(--muted-foreground))] text-left">
            Password
          </label>
          <div className="relative">
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
              className="absolute right-3 top-1/2 -translate-y-1/2 text-[hsl(var(--muted-foreground))] hover:text-[hsl(var(--foreground))] transition-colors cursor-pointer"
            >
              {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
            </button>
          </div>
        </div>

        <Button type="submit" className="w-full mt-4" disabled={loading}>
          {loading ? "Authenticating..." : "Sign In to Workspace"}
        </Button>
      </form>

      <div className="text-left text-xs text-[hsl(var(--muted-foreground))] pt-2">
        Need a new organization?{" "}
        <Link href="/auth/sign-up" className="text-[hsl(var(--primary))] hover:underline font-semibold">
          Register Organization
        </Link>
      </div>
    </div>
  );
}
