'use client';

import React, { useEffect, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { SignInForm } from '../../../components/auth/SignInForm';
import { authApiClient } from '../../../lib/auth-client';

export default function SignInPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const callbackUrl = searchParams.get('callbackUrl') ?? '/';

  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  useEffect(() => {
    document.cookie = 'authjs.session-token=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT';
    document.cookie = 'mock_role=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT';
  }, []);

  const handleSubmit = async (payload: { email: string; password?: string }) => {
    setLoading(true);
    setErrorMsg(null);

    try {
      const res = await authApiClient.signIn(payload as any);
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
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-[hsl(var(--background))] p-4 text-[hsl(var(--foreground))]">
      <SignInForm
        initialEmail="jaydeep@gmail.com"
        initialPassword="password12345"
        loading={loading}
        errorMsg={errorMsg}
        onSubmit={handleSubmit}
      />
    </div>
  );
}
