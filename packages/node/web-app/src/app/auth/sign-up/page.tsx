'use client';

import React, { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { SignUpForm } from '../../../components/auth/SignUpForm';
import { authApiClient } from '../../../lib/auth-client';

export default function SignUpPage() {
  const router = useRouter();
  const [loading, setLoading] = React.useState(false);
  const [errorMsg, setErrorMsg] = React.useState<string | null>(null);

  const handleSubmit = async (payload: { name: string; organization_name: string; email: string; password?: string }) => {
    setLoading(true);
    setErrorMsg(null);
    try {
      await authApiClient.signUp(payload as any);
      router.push('/auth/sign-in');
    } catch (err: any) {
      setErrorMsg(err?.message || 'Sign up failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-[hsl(var(--background))] p-4 text-[hsl(var(--foreground))]">
      <SignUpForm
        initialName="Jaydeep"
        initialOrgName="Scaibu"
        initialEmail="jaydeep@gmail.com"
        initialPassword="password12345"
        loading={loading}
        errorMsg={errorMsg}
        onSubmit={handleSubmit}
      />
    </div>
  );
}
