"use client";

import {
  useActionState,
} from "react";

import {
  retryWorkflow,
  type RetryState,
} from "./actions";


const initialState:
  RetryState = {
    success: false,
    error: null,
  };


export function RetryForm({
  errorId,
}: {
  errorId: string;
}) {
  const [
    state,
    action,
    pending,
  ] =
    useActionState(
      retryWorkflow,
      initialState,
    );

  return (
    <form
      action={action}
      className="mt-4 border-t border-slate-200 pt-4"
    >
      <input
        type="hidden"
        name="error_id"
        value={errorId}
      />

      <label className="block text-xs font-semibold uppercase tracking-wide text-slate-500">
        Retry reason
      </label>

      <textarea
        name="reason"
        required
        minLength={10}
        rows={2}
        placeholder="Explain why this workflow is being retried..."
        className="mt-2 w-full resize-none rounded-lg border border-slate-300 bg-white px-3 py-2.5 text-sm"
      />

      {state.error ? (
        <div className="mt-3 rounded-lg bg-red-50 px-3 py-2 text-xs text-red-700">
          {state.error}
        </div>
      ) : null}

      {state.success ? (
        <div className="mt-3 rounded-lg bg-emerald-50 px-3 py-2 text-xs text-emerald-700">
          Workflow recovered successfully.
        </div>
      ) : null}

      <button
        type="submit"
        disabled={pending}
        className="mt-3 rounded-lg bg-slate-950 px-4 py-2 text-sm font-medium text-white disabled:opacity-50"
      >
        {pending
          ? "Retrying..."
          : "Retry workflow"}
      </button>
    </form>
  );
}