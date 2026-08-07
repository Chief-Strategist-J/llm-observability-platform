'use client';

import React, { useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { Button } from '../../../components/primitives/Button';
import { Input } from '../../../components/primitives/Input';

export default function SignInPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const callbackUrl = searchParams.get('callbackUrl') ?? '/';

  const [email, setEmail] = useState('admin@acme.com');
  const [password, setPassword] = useState('password123');
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);

    try {
      document.cookie = 'authjs.session-token=mock-token; path=/';
      document.cookie = 'mock_role=owner; path=/';
      router.push(callbackUrl);
      router.refresh();
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-[hsl(var(--background))] p-4 text-[hsl(var(--foreground))]">
      <div className="w-full max-w-md rounded-[var(--radius-xl)] border border-[hsl(var(--border))] bg-[hsl(var(--card))] p-8 shadow-lg">
        <div className="mb-6 text-center">
          <h1 className="text-2xl font-bold tracking-tight">LLM Observability Platform</h1>
          <p className="mt-2 text-sm text-[hsl(var(--muted-foreground))]">
            Sign in to access your organization workspace
          </p>
        </div>

        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          <div className="flex flex-col gap-1.5">
            <label htmlFor="email" className="text-xs font-semibold uppercase text-[hsl(var(--muted-foreground))]">
              Email address
            </label>
            <Input
              id="email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </div>

          <div className="flex flex-col gap-1.5">
            <label htmlFor="password" className="text-xs font-semibold uppercase text-[hsl(var(--muted-foreground))]">
              Password
            </label>
            <Input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </div>

          <Button type="submit" className="mt-4 w-full" disabled={loading}>
            {loading ? 'Signing in...' : 'Sign in'}
          </Button>
        </form>
      </div>
    </div>
  );
}
