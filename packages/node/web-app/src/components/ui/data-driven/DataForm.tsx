"use client";

import React, { useState } from "react";

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
      className="space-y-4 rounded-xl border border-slate-800 bg-slate-900/60 p-6 backdrop-blur-md shadow-xl"
    >
      <h3 className="text-lg font-semibold text-slate-100 mb-4">{schema.name}</h3>

      {schema.fields.map((field) => (
        <div key={field.key} className="flex flex-col space-y-1.5">
          <label htmlFor={field.key} className="text-sm font-medium text-slate-300">
            {field.label} {field.required && <span className="text-rose-400">*</span>}
          </label>

          {field.kind === "text" || field.kind === "email" || field.kind === "password" ? (
            <input
              id={field.key}
              type={field.kind}
              required={field.required}
              value={values[field.key] || ""}
              onChange={(e) => handleChange(field.key, e.target.value)}
              className="rounded-lg border border-slate-700 bg-slate-950 px-3.5 py-2 text-sm text-slate-100 placeholder-slate-500 focus:border-cyan-500 focus:outline-none focus:ring-1 focus:ring-cyan-500 transition-all"
            />
          ) : field.kind === "select" ? (
            <select
              id={field.key}
              required={field.required}
              value={values[field.key] || ""}
              onChange={(e) => handleChange(field.key, e.target.value)}
              className="rounded-lg border border-slate-700 bg-slate-950 px-3.5 py-2 text-sm text-slate-100 focus:border-cyan-500 focus:outline-none focus:ring-1 focus:ring-cyan-500 transition-all"
            >
              <option value="">Select {field.label}...</option>
              {field.options?.map((opt) => (
                <option key={opt.value} value={opt.value}>
                  {opt.label}
                </option>
              ))}
            </select>
          ) : field.kind === "checkbox-group" ? (
            <div className="grid grid-cols-2 gap-2 rounded-lg border border-slate-800 bg-slate-950/80 p-3">
              {field.options?.map((opt) => {
                const currentArr: string[] = values[field.key] || [];
                const isChecked = currentArr.includes(opt.value);
                return (
                  <label key={opt.value} className="flex items-center space-x-2 text-xs text-slate-300 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={isChecked}
                      onChange={(e) => handleCheckboxGroup(field.key, opt.value, e.target.checked)}
                      className="rounded border-slate-700 bg-slate-900 text-cyan-500 focus:ring-cyan-500"
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
        <button
          type="submit"
          disabled={loading}
          className="w-full rounded-lg bg-gradient-to-r from-cyan-500 to-blue-600 px-4 py-2.5 text-sm font-medium text-white shadow-lg shadow-cyan-500/20 hover:from-cyan-400 hover:to-blue-500 disabled:opacity-50 transition-all"
        >
          {loading ? "Processing..." : submitLabel}
        </button>
      </div>
    </form>
  );
}
