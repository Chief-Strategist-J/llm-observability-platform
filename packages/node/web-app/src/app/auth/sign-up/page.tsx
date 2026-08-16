'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { Eye, EyeOff } from 'lucide-react';
import { authApiClient } from '../../../lib/auth-client';
import { Button } from '../../../components/primitives/Button';
import { Input } from '../../../components/primitives/Input';

export default function SignUpPage() {
  const router = useRouter();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [name, setName] = useState('');
  const [orgName, setOrgName] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const getPasswordStrength = (pass: string) => {
    if (!pass) return { label: '', score: 0, color: '' };
    if (pass.length < 8) return { label: 'Weak', score: 1, color: 'bg-[hsl(var(--destructive))]' };
    if (pass.length < 12) return { label: 'Medium', score: 2, color: 'bg-amber-500' };
    return { label: 'Strong', score: 3, color: 'bg-emerald-500' };
  };

  const strength = getPasswordStrength(password);

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
              placeholder="Jaydeep"
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
              placeholder="Scaibu"
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
              placeholder="jaydeep@gmail.com"
              required
            />
          </div>

          <div className="flex flex-col gap-1.5">
            <label htmlFor="password" className="text-xs font-semibold uppercase text-[hsl(var(--muted-foreground))]">
              Password (Min 12 chars)
            </label>
            <div className="relative">
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
                className="absolute right-3 top-1/2 -translate-y-1/2 text-[hsl(var(--muted-foreground))] hover:text-[hsl(var(--foreground))] transition-colors"
              >
                {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              </button>
            </div>

            {password && (
              <div className="space-y-1 pt-1">
                <div className="flex justify-between items-center text-[10px] text-[hsl(var(--muted-foreground))] font-medium">
                  <span>Strength: {strength.label}</span>
                </div>
                <div className="h-1 w-full bg-[hsl(var(--muted)/.3)] rounded-full overflow-hidden flex">
                  <div className={`h-full transition-all duration-300 ${strength.color} ${strength.score === 1 ? 'w-1/3' : strength.score === 2 ? 'w-2/3' : 'w-full'}`} />
                </div>
              </div>
            )}
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
