"use client";

import React, { useState } from "react";
import Link from "next/link";
import { Button } from "../../../components/primitives/Button";
import { Input } from "../../../components/primitives/Input";

export interface RegisterOrgFormProps {
  initialOrgName?: string;
  initialSlug?: string;
  loading?: boolean;
  errorMsg?: string | null;
  onSubmit: (payload: { name: string; slug?: string }) => void;
}

export function RegisterOrgForm({
  initialOrgName = "",
  initialSlug = "",
  loading = false,
  errorMsg = null,
  onSubmit,
}: RegisterOrgFormProps) {
  const [orgName, setOrgName] = useState(initialOrgName);
  const [slug, setSlug] = useState(initialSlug);

  return (
    <div className="auth-card">
      <div className="auth-header">
        <h1 className="auth-title">Step 1: Register Organization</h1>
        <p className="auth-subtitle">Create a new multi-tenant organization workspace</p>
      </div>

      {errorMsg && <div className="auth-error-alert">{errorMsg}</div>}

      <form
        onSubmit={(e) => {
          e.preventDefault();
          onSubmit({ name: orgName, slug });
        }}
        className="auth-form"
      >
        <div className="auth-field">
          <label htmlFor="orgName" className="auth-label">
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

        <div className="auth-field">
          <label htmlFor="slug" className="auth-label">
            Workspace Slug (Optional)
          </label>
          <Input
            id="slug"
            type="text"
            value={slug}
            onChange={(e) => setSlug(e.target.value)}
            placeholder="scaibu"
          />
        </div>

        <Button type="submit" className="auth-submit-btn" disabled={loading}>
          {loading ? "Registering Organization..." : "Register Organization & Proceed"}
        </Button>
      </form>

      <div className="auth-footer">
        Already registered?{" "}
        <Link href="/auth/sign-in" className="auth-footer-link">
          Sign In
        </Link>
      </div>
    </div>
  );
}
