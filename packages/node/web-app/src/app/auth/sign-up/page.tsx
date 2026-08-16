'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { authApiClient } from '../../../lib/auth-client';

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
    <div className="flex min-h-screen items-center justify-center bg-slate-950 p-4 text-slate-100">
      <div className="w-full max-w-md rounded-2xl border border-slate-800 bg-slate-900/60 p-8 backdrop-blur-md shadow-2xl space-y-6">
        <div className="text-center space-y-2">
          <h1 className="text-2xl font-bold tracking-tight bg-gradient-to-r from-cyan-400 to-blue-500 bg-clip-text text-transparent">
            Register Organization
          </h1>
          <p className="text-xs text-slate-400">
            Create your multi-tenant organization workspace
          </p>
        </div>

        {errorMsg && (
          <div className="rounded-lg border border-rose-800 bg-rose-950/60 p-3.5 text-xs text-rose-300">
            {errorMsg}
          </div>
        )}

        <form onSubmit={(e) => { void handleSubmit(e); }} className="space-y-4">
          <div className="space-y-1.5">
            <label htmlFor="name" className="text-xs font-semibold uppercase text-slate-400">
              Full Name
            </label>
            <input
              id="name"
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              required
              className="w-full rounded-lg border border-slate-700 bg-slate-950 px-3.5 py-2 text-sm text-slate-100 placeholder-slate-500 focus:border-cyan-500 focus:outline-none focus:ring-1 focus:ring-cyan-500 transition-all"
            />
          </div>

          <div className="space-y-1.5">
            <label htmlFor="orgName" className="text-xs font-semibold uppercase text-slate-400">
              Organization Name
            </label>
            <input
              id="orgName"
              type="text"
              value={orgName}
              onChange={(e) => setOrgName(e.target.value)}
              required
              className="w-full rounded-lg border border-slate-700 bg-slate-950 px-3.5 py-2 text-sm text-slate-100 placeholder-slate-500 focus:border-cyan-500 focus:outline-none focus:ring-1 focus:ring-cyan-500 transition-all"
            />
          </div>

          <div className="space-y-1.5">
            <label htmlFor="email" className="text-xs font-semibold uppercase text-slate-400">
              Email Address
            </label>
            <input
              id="email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              className="w-full rounded-lg border border-slate-700 bg-slate-950 px-3.5 py-2 text-sm text-slate-100 placeholder-slate-500 focus:border-cyan-500 focus:outline-none focus:ring-1 focus:ring-cyan-500 transition-all"
            />
          </div>

          <div className="space-y-1.5">
            <label htmlFor="password" className="text-xs font-semibold uppercase text-slate-400">
              Password (Min 12 chars)
            </label>
            <input
              id="password"
              type="password"
              value={password}
              minLength={12}
              onChange={(e) => setPassword(e.target.value)}
              required
              className="w-full rounded-lg border border-slate-700 bg-slate-950 px-3.5 py-2 text-sm text-slate-100 placeholder-slate-500 focus:border-cyan-500 focus:outline-none focus:ring-1 focus:ring-cyan-500 transition-all"
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full rounded-lg bg-gradient-to-r from-cyan-500 to-blue-600 px-4 py-2.5 text-sm font-medium text-white shadow-lg shadow-cyan-500/20 hover:from-cyan-400 hover:to-blue-500 disabled:opacity-50 transition-all"
          >
            {loading ? 'Creating Organization...' : 'Register Organization'}
          </button>
        </form>

        <div className="text-center text-xs text-slate-400 pt-2">
          Already have an organization?{" "}
          <Link href="/auth/sign-in" className="text-cyan-400 hover:underline">
            Sign In
          </Link>
        </div>
      </div>
    </div>
  );
}
