'use client';

import React, { useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { useRouter, useSearchParams } from 'next/navigation';
import { SignInForm, authActions, type AuthState, AUTH_DEFAULT_FIXTURES, AUTH_ROUTES } from '../../../features/auth';

export default function SignInPage() {
  const dispatch = useDispatch();
  const router = useRouter();
  const searchParams = useSearchParams();
  const callbackUrl = searchParams.get('callbackUrl') ?? AUTH_ROUTES.DASHBOARD;

  const { status, error } = useSelector((state: any) => (state.auth || {}) as AuthState);

  useEffect(() => {
    dispatch(authActions.resetAuthStatus());
    document.cookie = 'authjs.session-token=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT';
    document.cookie = 'user_role=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT';
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
    <div className="auth-container">
      <SignInForm
        initialEmail={AUTH_DEFAULT_FIXTURES.EMAIL}
        initialPassword={AUTH_DEFAULT_FIXTURES.PASSWORD}
        loading={status === 'loading'}
        errorMsg={error}
        onSubmit={handleSubmit}
      />
    </div>
  );
}
