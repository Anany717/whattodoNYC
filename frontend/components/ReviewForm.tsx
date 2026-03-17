"use client";

import { useState } from "react";

type ReviewValues = {
  rating_overall: number;
  rating_value?: number;
  rating_vibe?: number;
  rating_groupfit?: number;
  comment?: string;
};

type Props = {
  initialValues?: Partial<ReviewValues>;
  submitLabel?: string;
  onSubmit: (values: ReviewValues) => Promise<void>;
};

export default function ReviewForm({ initialValues, submitLabel = "Save Review", onSubmit }: Props) {
  const [values, setValues] = useState<ReviewValues>({
    rating_overall: initialValues?.rating_overall ?? 5,
    rating_value: initialValues?.rating_value,
    rating_vibe: initialValues?.rating_vibe,
    rating_groupfit: initialValues?.rating_groupfit,
    comment: initialValues?.comment || ""
  });
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const setField = (key: keyof ReviewValues, value: string) => {
    setValues((prev) => ({
      ...prev,
      [key]: value === "" ? undefined : key === "comment" ? value : Number(value)
    }));
  };

  return (
    <form
      className="card space-y-3 p-4"
      onSubmit={async (event) => {
        event.preventDefault();
        setError(null);
        setSubmitting(true);
        try {
          await onSubmit(values);
        } catch (err) {
          setError((err as Error).message);
        } finally {
          setSubmitting(false);
        }
      }}
    >
      <div className="grid gap-3 sm:grid-cols-2">
        {[
          ["rating_overall", "Overall"],
          ["rating_value", "Value"],
          ["rating_vibe", "Vibe"],
          ["rating_groupfit", "Group fit"]
        ].map(([key, label]) => (
          <label key={key} className="text-sm font-medium text-slate-700">
            {label}
            <input
              type="number"
              min={1}
              max={5}
              required={key === "rating_overall"}
              value={values[key as keyof ReviewValues] ?? ""}
              onChange={(event) => setField(key as keyof ReviewValues, event.target.value)}
              className="field-input mt-1"
            />
          </label>
        ))}
      </div>

      <label className="text-sm font-medium text-slate-700">
        Comment
        <textarea
          value={values.comment || ""}
          onChange={(event) => setField("comment", event.target.value)}
          rows={3}
          className="field-input mt-1"
          placeholder="Share your experience"
        />
      </label>

      {error ? <p className="text-sm text-red-600">{error}</p> : null}

      <button
        disabled={submitting}
        className="btn-primary disabled:opacity-60"
      >
        {submitting ? "Saving..." : submitLabel}
      </button>
    </form>
  );
}
