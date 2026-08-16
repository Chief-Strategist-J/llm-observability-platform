"use client";

import React, { useState } from "react";
import Link from "next/link";
import { Button } from "../primitives/Button";
import { Input } from "../primitives/Input";

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
    <div className="w-full max-w-md rounded-[var(--radius-xl)] border border-[hsl(var(--border))] bg-[hsl(var(--card))] p-8 shadow-lg space-y-6 text-left">
      <div className="text-left space-y-1.5 mb-6">
        <h1 className="text-2xl font-bold tracking-tight text-[hsl(var(--foreground))] text-left">
          Step 1: Register Organization
        </h1>
        <p className="text-xs text-[hsl(var(--muted-foreground))] text-left">
          Create a new multi-tenant organization workspace
        </p>
      </div>

      {errorMsg && (
        <div className="rounded-[var(--radius-md)] border border-[hsl(var(--destructive)/.4)] bg-[hsl(var(--destructive)/.15)] p-3.5 text-xs text-[hsl(var(--destructive))] font-medium text-left">
          {errorMsg}
        </div>
      )}

      <form
        onSubmit={(e) => {
          e.preventDefault();
          onSubmit({ name: orgName, slug });
        }}
        className="space-y-4 text-left"
      >
        <div className="flex flex-col gap-1.5 text-left">
          <label htmlFor="orgName" className="text-xs font-semibold uppercase text-[hsl(var(--muted-foreground))] text-left">
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

        <div className="flex flex-col gap-1.5 text-left">
          <label htmlFor="slug" className="text-xs font-semibold uppercase text-[hsl(var(--muted-foreground))] text-left">
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

        <Button type="submit" className="w-full mt-4" disabled={loading}>
          {loading ? "Registering Organization..." : "Register Organization & Proceed"}
        </Button>
      </form>

      <div className="text-left text-xs text-[hsl(var(--muted-foreground))] pt-2">
        Already registered?{" "}
        <Link href="/auth/sign-in" className="text-[hsl(var(--primary))] hover:underline font-semibold">
          Sign In
        </Link>
      </div>
    </div>
  );
}
