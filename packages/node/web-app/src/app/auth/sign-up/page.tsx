'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { authApiClient } from '../../../lib/auth-client';
import { Button } from '../../../components/primitives/Button';
import { Input } from '../../../components/primitives/Input';

export default function SignUpPage() {
  const router = useRouter();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [name, setName] = useState('');
  const [orgName, setOrgName] = useState('');
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setErrorMsg(null);

    try {
      await authApiClient.signUp({
        email,
        password,
        name,
        organization_name: orgName,
        role: 'admin',
      });
      router.push('/auth/sign-in');
    } catch (err: any) {
      setErrorMsg(err?.message || 'Sign up failed. Please try again.');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-[hsl(var(--background))] p-4 text-[hsl(var(--foreground))]">
      <div className="w-full max-w-md rounded-[var(--radius-xl)] border border-[hsl(var(--border))] bg-[hsl(var(--card))] p-8 shadow-lg space-y-6">
        <div className="text-center space-y-2 mb-6">
          <h1 className="text-2xl font-bold tracking-tight text-[hsl(var(--foreground))]">
            Register Organization
          </h1>
          <p className="text-xs text-[hsl(var(--muted-foreground))]">
            Create your multi-tenant organization workspace
          </p>
        </div>

        {errorMsg && (
          <div className="rounded-[var(--radius-md)] border border-[hsl(var(--destructive)/.4)] bg-[hsl(var(--destructive)/.15)] p-3.5 text-xs text-[hsl(var(--destructive))] font-medium">
            {errorMsg}
          </div>
        )}

        <form onSubmit={(e) => { void handleSubmit(e); }} className="space-y-4">
          <div className="flex flex-col gap-1.5">
            <label htmlFor="name" className="text-xs font-semibold uppercase text-[hsl(var(--muted-foreground))]">
              Full Name
            </label>
            <Input
              id="name"
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="John Doe"
              required
            />
          </div>

          <div className="flex flex-col gap-1.5">
            <label htmlFor="orgName" className="text-xs font-semibold uppercase text-[hsl(var(--muted-foreground))]">
              Organization Name
            </label>
            <Input
              id="orgName"
              type="text"
              value={orgName}
              onChange={(e) => setOrgName(e.target.value)}
              placeholder="Acme Corporation"
              required
            />
          </div>

          <div className="flex flex-col gap-1.5">
            <label htmlFor="email" className="text-xs font-semibold uppercase text-[hsl(var(--muted-foreground))]">
              Email Address
            </label>
            <Input
              id="email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="admin@acme.com"
              required
            />
          </div>

          <div className="flex flex-col gap-1.5">
            <label htmlFor="password" className="text-xs font-semibold uppercase text-[hsl(var(--muted-foreground))]">
              Password (Min 12 chars)
            </label>
            <Input
              id="password"
              type="password"
              value={password}
              minLength={12}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••••••"
              required
            />
          </div>

          <Button type="submit" className="w-full mt-4" disabled={loading}>
            {loading ? 'Creating Organization...' : 'Register Organization'}
          </Button>
        </form>

        <div className="text-center text-xs text-[hsl(var(--muted-foreground))] pt-2">
          Already have an organization?{" "}
          <Link href="/auth/sign-in" className="text-[hsl(var(--primary))] hover:underline font-semibold">
            Sign In
          </Link>
        </div>
      </div>
    </div>
  );
}
