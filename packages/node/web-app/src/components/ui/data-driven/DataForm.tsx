"use client";

import React, { useState } from "react";
import { Button } from "../../primitives/Button";
import { Input } from "../../primitives/Input";

export interface FieldConfig {
  key: string;
  label: string;
  kind: "text" | "email" | "password" | "select" | "checkbox-group";
  required?: boolean;
  options?: Array<{ label: string; value: string }>;
  defaultValue?: any;
}

export interface SchemaConfig {
  name: string;
  fields: FieldConfig[];
}

export function DataForm<T extends Record<string, any>>({
  schema,
  initialValues = {} as Partial<T>,
  onSubmit,
  submitLabel = "Save",
  loading = false,
}: {
  schema: SchemaConfig;
  initialValues?: Partial<T>;
  onSubmit: (values: T) => void;
  submitLabel?: string;
  loading?: boolean;
}) {
  const [values, setValues] = useState<Record<string, any>>(() => {
    const defaults: Record<string, any> = { ...initialValues };
    schema.fields.forEach((f) => {
      if (defaults[f.key] === undefined && f.defaultValue !== undefined) {
        defaults[f.key] = f.defaultValue;
      }
    });
    return defaults;
  });

  const handleChange = (key: string, val: any) => {
    setValues((prev) => ({ ...prev, [key]: val }));
  };

  const handleCheckboxGroup = (key: string, val: string, checked: boolean) => {
    setValues((prev) => {
      const existing: string[] = prev[key] || [];
      if (checked) {
        return { ...prev, [key]: [...new Set([...existing, val])] };
      } else {
        return { ...prev, [key]: existing.filter((item) => item !== val) };
      }
    });
  };

  return (
    <form
      onSubmit={(e) => {
        e.preventDefault();
        onSubmit(values as T);
      }}
      className="space-y-4 rounded-[var(--radius-xl)] border border-[hsl(var(--border))] bg-[hsl(var(--card))] p-6 shadow-md text-[hsl(var(--card-foreground))]"
    >
      <h3 className="text-lg font-bold tracking-tight text-[hsl(var(--foreground))]">{schema.name}</h3>

      {schema.fields.map((field) => (
        <div key={field.key} className="flex flex-col space-y-1.5">
          <label htmlFor={field.key} className="text-xs font-semibold uppercase text-[hsl(var(--muted-foreground))]">
            {field.label} {field.required && <span className="text-[hsl(var(--destructive))]">*</span>}
          </label>

          {field.kind === "text" || field.kind === "email" || field.kind === "password" ? (
            <Input
              id={field.key}
              type={field.kind}
              required={field.required}
              value={values[field.key] || ""}
              onChange={(e) => handleChange(field.key, e.target.value)}
            />
          ) : field.kind === "select" ? (
            <select
              id={field.key}
              required={field.required}
              value={values[field.key] || ""}
              onChange={(e) => handleChange(field.key, e.target.value)}
              className="w-full rounded-[var(--radius-md)] border border-[hsl(var(--border))] bg-[hsl(var(--background))] px-3.5 py-2 text-sm text-[hsl(var(--foreground))] focus:outline-none focus:ring-2 focus:ring-[hsl(var(--ring))]"
            >
              <option value="">Select {field.label}...</option>
              {field.options?.map((opt) => (
                <option key={opt.value} value={opt.value}>
                  {opt.label}
                </option>
              ))}
            </select>
          ) : field.kind === "checkbox-group" ? (
            <div className="grid grid-cols-2 gap-2 rounded-[var(--radius-md)] border border-[hsl(var(--border))] bg-[hsl(var(--muted)/.2)] p-3">
              {field.options?.map((opt) => {
                const currentArr: string[] = values[field.key] || [];
                const isChecked = currentArr.includes(opt.value);
                return (
                  <label key={opt.value} className="flex items-center space-x-2 text-xs text-[hsl(var(--foreground))] cursor-pointer">
                    <input
                      type="checkbox"
                      checked={isChecked}
                      onChange={(e) => handleCheckboxGroup(field.key, opt.value, e.target.checked)}
                      className="rounded border-[hsl(var(--border))] text-[hsl(var(--primary))]"
                    />
                    <span>{opt.label}</span>
                  </label>
                );
              })}
            </div>
          ) : null}
        </div>
      ))}

      <div className="pt-2">
        <Button type="submit" variant="gradient" className="w-full font-bold" disabled={loading}>
          {loading ? "Processing..." : submitLabel}
        </Button>
      </div>
    </form>
  );
}
