'use client';

import React, { useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { useRouter } from 'next/navigation';
import { SignUpForm, authActions, type AuthState, AUTH_DEFAULT_FIXTURES, AUTH_ROUTES } from '../../../features/auth';

export default function SignUpPage() {
  const dispatch = useDispatch();
  const router = useRouter();

  const { status, error } = useSelector((state: any) => (state.auth || {}) as AuthState);

  useEffect(() => {
    dispatch(authActions.resetAuthStatus());
  }, [dispatch]);

  useEffect(() => {
    if (status === 'success') {
      router.push(AUTH_ROUTES.SIGN_IN);
    }
  }, [status, router]);

  const handleSubmit = (payload: { name: string; organization_name: string; email: string; password?: string }) => {
    dispatch(authActions.signUpSubmitted(payload as any));
  };

  return (
    <div className="auth-container">
      <SignUpForm
        initialName={AUTH_DEFAULT_FIXTURES.NAME}
        initialOrgName={AUTH_DEFAULT_FIXTURES.ORG_NAME}
        initialEmail={AUTH_DEFAULT_FIXTURES.EMAIL}
        initialPassword={AUTH_DEFAULT_FIXTURES.PASSWORD}
        loading={status === 'loading'}
        errorMsg={error}
        onSubmit={handleSubmit}
      />
    </div>
  );
}
