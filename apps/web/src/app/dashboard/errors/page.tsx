import Link from "next/link";

import {
  getCurrentOperatorRole,
  getWorkflowErrors,
} from "@/lib/data/errors";

import {
  RetryForm,
} from "./retry-form";


function formatDate(
  value: string,
) {
  return new Date(
    value,
  ).toLocaleString();
}


export default async function
WorkflowErrorsPage() {

  const [
    errors,
    role,
  ] =
    await Promise.all([
      getWorkflowErrors(),
      getCurrentOperatorRole(),
    ]);

  const openCount =
    errors.filter(
      (item) =>
        item.status === "OPEN",
    ).length;

  const retryingCount =
    errors.filter(
      (item) =>
        item.status
          === "RETRYING",
    ).length;

  const deadLetterCount =
    errors.filter(
      (item) =>
        item.status
          === "DEAD_LETTER",
    ).length;

  const canRetry =
    role === "ADMIN";

  return (
    <div className="space-y-6">

      <div>
        <h1 className="text-2xl font-semibold text-slate-950">
          Workflow Errors
        </h1>

        <p className="mt-1 text-sm text-slate-500">
          Investigate failed automation
          steps and safely reprocess
          unresolved leads.
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-3">

        <SummaryCard
          label="Open"
          value={openCount}
        />

        <SummaryCard
          label="Retrying"
          value={retryingCount}
        />

        <SummaryCard
          label="Dead letter"
          value={deadLetterCount}
        />

      </div>

      {errors.length === 0 ? (

        <div className="rounded-xl border border-slate-200 bg-white p-10 text-center">

          <div className="text-lg font-medium text-slate-900">
            No unresolved workflow errors
          </div>

          <p className="mt-2 text-sm text-slate-500">
            All recorded automation
            workflows are currently clear.
          </p>

        </div>

      ) : (

        <div className="space-y-4">

          {errors.map(
            (item) => (

              <article
                key={item.id}
                className="rounded-xl border border-slate-200 bg-white p-5"
              >

                <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">

                  <div>

                    <div className="flex flex-wrap items-center gap-2">

                      <span className="rounded-full bg-red-50 px-2.5 py-1 text-xs font-semibold text-red-700">
                        {item.status}
                      </span>

                      <span className="text-xs text-slate-400">
                        {item.provider ??
                          "internal"}
                      </span>

                      {item.retryable ? (
                        <span className="rounded-full bg-amber-50 px-2.5 py-1 text-xs font-medium text-amber-700">
                          Retryable
                        </span>
                      ) : null}

                    </div>

                    <h2 className="mt-3 text-lg font-semibold text-slate-950">
                      {item.lead
                        ?.full_name ??
                        "Unknown lead"}
                    </h2>

                    <p className="mt-1 font-mono text-xs text-slate-500">
                      {item.error_code}
                    </p>

                  </div>

                  <Link
                    href={
                      `/dashboard/leads/${item.lead_id}`
                    }
                    className="text-sm font-medium text-slate-700 underline underline-offset-4"
                  >
                    Inspect lead
                  </Link>

                </div>

                {item.error_message ? (
                  <div className="mt-4 rounded-lg bg-red-50 p-3 text-sm leading-6 text-red-800">
                    {item.error_message}
                  </div>
                ) : null}

                <dl className="mt-5 grid gap-4 text-sm md:grid-cols-2 lg:grid-cols-4">

                  <Detail
                    label="Failed action"
                    value={
                      item.failed_action
                    }
                  />

                  <Detail
                    label="Lead status"
                    value={
                      item.lead?.status ??
                      "—"
                    }
                  />

                  <Detail
                    label="Retry count"
                    value={String(
                      item.retry_count,
                    )}
                  />

                  <Detail
                    label="Created"
                    value={formatDate(
                      item.created_at,
                    )}
                  />

                </dl>

                <div className="mt-4 text-xs text-slate-400">
                  Correlation ID:{" "}
                  <span className="font-mono">
                    {item.correlation_id}
                  </span>
                </div>

                {canRetry ? (
                  <RetryForm
                    errorId={item.id}
                  />
                ) : (
                  <div className="mt-4 border-t border-slate-200 pt-4 text-xs text-slate-500">
                    Administrator permission
                    is required to retry this
                    workflow.
                  </div>
                )}

              </article>

            ),
          )}

        </div>

      )}

    </div>
  );
}


function SummaryCard({
  label,
  value,
}: {
  label: string;
  value: number;
}) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-5">
      <div className="text-sm text-slate-500">
        {label}
      </div>

      <div className="mt-2 text-3xl font-semibold text-slate-950">
        {value}
      </div>
    </div>
  );
}


function Detail({
  label,
  value,
}: {
  label: string;
  value: string;
}) {
  return (
    <div>
      <dt className="text-xs font-medium uppercase tracking-wide text-slate-400">
        {label}
      </dt>

      <dd className="mt-1 wrap-break-word text-slate-800">
        {value}
      </dd>
    </div>
  );
}