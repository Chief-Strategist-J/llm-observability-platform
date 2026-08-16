'use client';

import React, { useState, useEffect } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import Link from 'next/link';
import { Eye, EyeOff } from 'lucide-react';
import { authApiClient } from '../../../lib/auth-client';
import { Button } from '../../../components/primitives/Button';
import { Input } from '../../../components/primitives/Input';

export default function SignInPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const callbackUrl = searchParams.get('callbackUrl') ?? '/';

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  useEffect(() => {
    document.cookie = 'authjs.session-token=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT';
    document.cookie = 'mock_role=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT';
  }, []);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setErrorMsg(null);

    try {
      const res = await authApiClient.signIn({ email, password });
      document.cookie = `authjs.session-token=${res.token}; path=/`;
      document.cookie = `mock_role=${res.user.role || "owner"}; path=/`;
      router.push(callbackUrl);
      router.refresh();
    } catch (err: any) {
      if (err?.code === "USER_BLOCKED" || err?.message?.includes("blocked")) {
        setErrorMsg("Access Denied: Your user account has been blocked by your organization administrator.");
      } else {
        setErrorMsg(err?.message || "Invalid credentials. Please enter valid email and password.");
      }
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-[hsl(var(--background))] p-4 text-[hsl(var(--foreground))]">
      <div className="w-full max-w-md rounded-[var(--radius-xl)] border border-[hsl(var(--border))] bg-[hsl(var(--card))] p-8 shadow-lg space-y-6">
        <div className="text-center space-y-2">
          <h1 className="text-2xl font-bold tracking-tight text-[hsl(var(--foreground))]">
            LLM Observability Platform
          </h1>
          <p className="text-xs text-[hsl(var(--muted-foreground))]">
            Sign in to access your multi-tenant observability workspace
          </p>
        </div>

        {errorMsg && (
          <div className="rounded-[var(--radius-md)] border border-[hsl(var(--destructive)/.4)] bg-[hsl(var(--destructive)/.15)] p-3.5 text-xs text-[hsl(var(--destructive))] font-medium">
            {errorMsg}
          </div>
        )}

        <form onSubmit={(e) => { void handleSubmit(e); }} className="space-y-4">
          <div className="space-y-1.5">
            <label htmlFor="email" className="text-xs font-semibold uppercase text-[hsl(var(--muted-foreground))]">
              Email address
            </label>
            <Input
              id="email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              placeholder="user@organization.com"
            />
          </div>

          <div className="space-y-1.5">
            <label htmlFor="password" className="text-xs font-semibold uppercase text-[hsl(var(--muted-foreground))]">
              Password
            </label>
            <div className="relative">
              <Input
                id="password"
                type={showPassword ? "text" : "password"}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                placeholder="••••••••••••"
                className="pr-10"
              />
              <button
                type="button"
                aria-label={showPassword ? "Hide password" : "Show password"}
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-[hsl(var(--muted-foreground))] hover:text-[hsl(var(--foreground))] transition-colors"
              >
                {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              </button>
            </div>
          </div>

          <Button type="submit" className="w-full mt-2" disabled={loading}>
            {loading ? 'Authenticating...' : 'Sign in'}
          </Button>
        </form>

        <div className="text-center text-xs text-[hsl(var(--muted-foreground))] pt-2">
          Need a new organization?{" "}
          <Link href="/auth/sign-up" className="text-[hsl(var(--primary))] hover:underline font-semibold">
            Register Organization
          </Link>
        </div>
      </div>
    </div>
  );
}
