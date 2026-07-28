"use client";

import Link from "next/link";

export default function DashboardError({
  reset,
}: {
  error: Error & {
    digest?: string;
  };
  reset: () => void;
}) {
  return (
    <div className="flex min-h-[60vh] items-center justify-center">
      <div
        role="alert"
        className="w-full max-w-xl rounded-2xl border border-red-200 bg-white p-8"
      >
        <p className="text-sm font-semibold text-red-700">
          Dashboard unavailable
        </p>

        <h1 className="mt-2 text-2xl font-semibold text-slate-950">
          Operational data could not be loaded.
        </h1>

        <p className="mt-3 text-sm leading-6 text-slate-600">
          The request failed safely. Retry the page, or return to the dashboard after checking the API and database services.
        </p>

        <div className="mt-6 flex flex-wrap gap-3">
          <button
            type="button"
            onClick={reset}
            className="rounded-lg bg-slate-950 px-4 py-2 text-sm font-medium text-white"
          >
            Retry
          </button>

          <Link
            href="/dashboard"
            className="rounded-lg border border-slate-300 bg-white px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
          >
            Dashboard home
          </Link>
        </div>
      </div>
    </div>
  );
}
