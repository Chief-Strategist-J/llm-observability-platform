'use client';

import React, { useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { useRouter, useSearchParams } from 'next/navigation';
import { SignInForm } from '../../../components/auth/SignInForm';
import { authActions, type AuthState } from '../../../features/auth/auth.slice';

export default function SignInPage() {
  const dispatch = useDispatch();
  const router = useRouter();
  const searchParams = useSearchParams();
  const callbackUrl = searchParams.get('callbackUrl') ?? '/';

  const { status, error } = useSelector((state: any) => (state.auth || {}) as AuthState);

  useEffect(() => {
    dispatch(authActions.resetAuthStatus());
    document.cookie = 'authjs.session-token=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT';
    document.cookie = 'mock_role=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT';
  }, [dispatch]);

  useEffect(() => {
    if (status === 'success') {
      router.push(callbackUrl);
      router.refresh();
    }
  }, [status, router, callbackUrl]);

  const handleSubmit = (payload: { email: string; password?: string }) => {
    dispatch(authActions.signInSubmitted(payload as any));
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-[hsl(var(--background))] p-4 text-[hsl(var(--foreground))]">
      <SignInForm
        initialEmail="jaydeep@gmail.com"
        initialPassword="password12345"
        loading={status === 'loading'}
        errorMsg={error}
        onSubmit={handleSubmit}
      />
    </div>
  );
}
