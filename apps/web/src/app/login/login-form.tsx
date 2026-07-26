"use client";

import { useActionState } from "react";

import {
  login,
  type LoginState,
} from "./actions";

const initialState: LoginState = {
  error: null,
};

export function LoginForm() {
  const [
    state,
    formAction,
    pending,
  ] = useActionState(
    login,
    initialState,
  );

  return (
    <form
      action={formAction}
      className="mt-8 space-y-5"
    >
      <div>
        <label
          htmlFor="email"
          className="mb-2 block text-sm font-medium text-slate-700"
        >
          Email
        </label>

        <input
          id="email"
          name="email"
          type="email"
          autoComplete="email"
          required
          className="w-full rounded-lg border border-slate-300 px-4 py-3 text-slate-950 outline-none transition focus:border-slate-900"
          placeholder="operator@northstar.local"
        />
      </div>

      <div>
        <label
          htmlFor="password"
          className="mb-2 block text-sm font-medium text-slate-700"
        >
          Password
        </label>

        <input
          id="password"
          name="password"
          type="password"
          autoComplete="current-password"
          required
          className="w-full rounded-lg border border-slate-300 px-4 py-3 text-slate-950 outline-none transition focus:border-slate-900"
          placeholder="••••••••"
        />
      </div>

      {state.error ? (
        <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          {state.error}
        </div>
      ) : null}

      <button
        type="submit"
        disabled={pending}
        className="w-full rounded-lg bg-slate-950 px-4 py-3 font-medium text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-60"
      >
        {pending
          ? "Signing in..."
          : "Sign in"}
      </button>
    </form>
  );
}