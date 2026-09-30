"use client";

import { Save } from "lucide-react";
import { FormEvent, useMemo, useState } from "react";
import { z } from "zod";
import type { FieldConfig } from "@/lib/resource-config";
import { valueLabelAr } from "@/lib/labels";

type FormState = Record<string, string>;

export function ResourceForm({
  fields,
  schema,
  initial,
  submitLabel = "حفظ",
  onSubmit
}: {
  fields: FieldConfig[];
  schema: z.ZodTypeAny;
  initial?: Record<string, unknown>;
  submitLabel?: string;
  onSubmit: (payload: Record<string, unknown>) => void;
}) {
  const initialState = useMemo(() => {
    const state: FormState = {};
    fields.forEach((field) => {
      state[field.name] = initial?.[field.name] === undefined ? "" : String(initial[field.name]);
    });
    return state;
  }, [fields, initial]);
  const [values, setValues] = useState<FormState>(initialState);
  const [errors, setErrors] = useState<Record<string, string>>({});

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const payload = Object.fromEntries(
      Object.entries(values).map(([key, value]) => [key, value === "" ? undefined : value])
    );
    const result = schema.safeParse(payload);
    if (!result.success) {
      const next: Record<string, string> = {};
      result.error.issues.forEach((issue) => {
        next[String(issue.path[0])] = issue.message;
      });
      setErrors(next);
      return;
    }
    setErrors({});
    onSubmit(result.data as Record<string, unknown>);
  }

  return (
    <form onSubmit={handleSubmit}>
      <div className="form-grid">
        {fields.map((field) => (
          <div className={`field ${field.full ? "full" : ""}`} key={field.name}>
            <label htmlFor={field.name}>
              {field.label}
              {field.required ? " *" : ""}
            </label>
            {field.type === "textarea" ? (
              <textarea
                className="textarea"
                id={field.name}
                value={values[field.name] ?? ""}
                onChange={(event) => setValues((current) => ({ ...current, [field.name]: event.target.value }))}
              />
            ) : field.type === "select" ? (
              <select
                className="select"
                id={field.name}
                value={values[field.name] ?? ""}
                onChange={(event) => setValues((current) => ({ ...current, [field.name]: event.target.value }))}
              >
                <option value="">اختر</option>
                {field.options?.map((option) => (
                  <option key={option} value={option}>
                    {valueLabelAr(option)}
                  </option>
                ))}
              </select>
            ) : (
              <input
                className="input"
                id={field.name}
                type={field.type === "number" ? "number" : "text"}
                value={values[field.name] ?? ""}
                onChange={(event) => setValues((current) => ({ ...current, [field.name]: event.target.value }))}
              />
            )}
            {errors[field.name] && <span className="error">{errors[field.name]}</span>}
          </div>
        ))}
      </div>
      <div className="panel-header" style={{ borderTop: "1px solid var(--hairline)", borderBottom: 0 }}>
        <button className="button primary" type="submit">
          <Save size={16} />
          {submitLabel}
        </button>
      </div>
    </form>
  );
}
