"use client";

import {
  useActionState,
} from "react";

import {
  resolveReview,
  type ReviewActionState,
} from "./actions";


const initialState:
  ReviewActionState = {
    success: false,
    error: null,
  };


export function ReviewResolutionForm({
  leadId,
}: {
  leadId: string;
}) {
  const [
    state,
    formAction,
    pending,
  ] = useActionState(
    resolveReview,
    initialState,
  );

  return (
    <form
      action={formAction}
      className="mt-5 rounded-lg border border-slate-200 bg-slate-50 p-4"
    >
      <input
        type="hidden"
        name="lead_id"
        value={leadId}
      />

      <label className="block text-xs font-semibold uppercase tracking-wide text-slate-500">
        Decision
      </label>

      <select
        name="status"
        required
        defaultValue=""
        className="mt-2 w-full rounded-lg border border-slate-300 bg-white px-3 py-2.5 text-sm text-slate-800"
      >
        <option
          value=""
          disabled
        >
          Select decision
        </option>

        <option value="QUALIFIED_HOT">
          Approve as Hot
        </option>

        <option value="QUALIFIED_WARM">
          Approve as Warm
        </option>

        <option value="COLD">
          Mark Cold
        </option>

        <option value="DISQUALIFIED">
          Disqualify
        </option>
      </select>

      <label className="mt-4 block text-xs font-semibold uppercase tracking-wide text-slate-500">
        Reason
      </label>

      <textarea
        name="reason"
        required
        minLength={10}
        rows={3}
        placeholder="Explain why you are overriding the automated decision..."
        className="mt-2 w-full resize-none rounded-lg border border-slate-300 bg-white px-3 py-2.5 text-sm text-slate-800"
      />

      {state.error ? (
        <div className="mt-3 rounded-lg bg-red-50 px-3 py-2 text-xs text-red-700">
          {state.error}
        </div>
      ) : null}

      <button
        type="submit"
        disabled={pending}
        className="mt-4 w-full rounded-lg bg-slate-950 px-4 py-2.5 text-sm font-medium text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-50"
      >
        {pending
          ? "Resolving..."
          : "Resolve review"}
      </button>
    </form>
  );
}