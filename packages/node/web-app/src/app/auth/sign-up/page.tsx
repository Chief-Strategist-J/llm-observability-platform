'use client';

import React, { useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { useRouter } from 'next/navigation';
import { SignUpForm } from '../../../components/auth/SignUpForm';
import { authActions, type AuthState } from '../../../features/auth/auth.slice';

export default function SignUpPage() {
  const dispatch = useDispatch();
  const router = useRouter();

  const { status, error } = useSelector((state: any) => (state.auth || {}) as AuthState);

  useEffect(() => {
    dispatch(authActions.resetAuthStatus());
  }, [dispatch]);

  useEffect(() => {
    if (status === 'success') {
      router.push('/auth/sign-in');
    }
  }, [status, router]);

  const handleSubmit = (payload: { name: string; organization_name: string; email: string; password?: string }) => {
    dispatch(authActions.signUpSubmitted(payload as any));
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-[hsl(var(--background))] p-4 text-[hsl(var(--foreground))]">
      <SignUpForm
        initialName="Jaydeep"
        initialOrgName="Scaibu"
        initialEmail="jaydeep@gmail.com"
        initialPassword="password12345"
        loading={status === 'loading'}
        errorMsg={error}
        onSubmit={handleSubmit}
      />
    </div>
  );
}
