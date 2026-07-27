"use client";

import {
  useActionState,
} from "react";

import {
  importLeadCsv,
  type CsvImportState,
} from "./actions";


const initialState:
  CsvImportState = {
    success: false,
    error: null,

    total: 0,
    succeeded: 0,
    failed: 0,
    duplicates: 0,

    results: [],
  };


export function CsvImportForm() {

  const [
    state,
    action,
    pending,
  ] =
    useActionState(
      importLeadCsv,
      initialState,
    );

  return (
    <div className="rounded-xl border border-slate-200 bg-white p-6">

      <h2 className="text-lg font-semibold text-slate-950">
        CSV test import
      </h2>

      <p className="mt-1 text-sm leading-6 text-slate-500">
        Import up to 100 synthetic leads.
        Each row enters the canonical
        pipeline independently using the
        CSV test source.
      </p>

      <div className="mt-5 rounded-lg bg-slate-50 p-4">

        <div className="text-xs font-semibold uppercase tracking-wide text-slate-500">
          CSV columns
        </div>

        <code className="mt-2 block overflow-x-auto whitespace-nowrap text-xs text-slate-700">
          full_name,email,phone,service_type,location,urgency,message,preferred_contact,consent_marketing
        </code>

      </div>

      <form
        action={action}
        className="mt-5"
      >
        <input
          type="file"
          name="file"
          accept=".csv,text/csv"
          required
          className="block w-full rounded-lg border border-slate-300 bg-white p-2 text-sm"
        />

        <div className="mt-3 text-xs leading-5 text-amber-700">
          Imported rows use your currently
          configured integrations. Qualified
          test leads can trigger HubSpot,
          email, Slack and other automation.
        </div>

        <button
          type="submit"
          disabled={pending}
          className="mt-4 rounded-lg bg-slate-950 px-5 py-2.5 text-sm font-medium text-white disabled:cursor-not-allowed disabled:opacity-50"
        >
          {pending
            ? "Importing..."
            : "Import CSV"}
        </button>
      </form>

      {state.error ? (
        <div className="mt-5 rounded-lg bg-red-50 p-3 text-sm text-red-700">
          {state.error}
        </div>
      ) : null}

      {state.results.length > 0 ? (
        <div className="mt-6">

          <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">

            <Metric
              label="Rows"
              value={state.total}
            />

            <Metric
              label="Accepted"
              value={state.succeeded}
            />

            <Metric
              label="Failed"
              value={state.failed}
            />

            <Metric
              label="Duplicates"
              value={state.duplicates}
            />

          </div>

          <div className="mt-5 overflow-x-auto rounded-lg border border-slate-200">

            <table className="min-w-full divide-y divide-slate-200 text-sm">

              <thead className="bg-slate-50 text-left text-xs uppercase tracking-wide text-slate-500">
                <tr>
                  <th className="px-4 py-3">
                    Row
                  </th>

                  <th className="px-4 py-3">
                    Lead
                  </th>

                  <th className="px-4 py-3">
                    Result
                  </th>

                  <th className="px-4 py-3">
                    Status
                  </th>

                  <th className="px-4 py-3">
                    Detail
                  </th>
                </tr>
              </thead>

              <tbody className="divide-y divide-slate-100 bg-white">

                {state.results.map(
                  (result) => (

                    <tr
                      key={
                        `${result.row}-${result.name}`
                      }
                    >

                      <td className="px-4 py-3 text-slate-500">
                        {result.row}
                      </td>

                      <td className="px-4 py-3 font-medium text-slate-900">
                        {result.name}
                      </td>

                      <td className="px-4 py-3">
                        {result.success
                          ? "Accepted"
                          : "Failed"}
                      </td>

                      <td className="px-4 py-3">
                        {result.status ??
                          "—"}
                      </td>

                      <td className="max-w-md px-4 py-3 text-xs leading-5 text-slate-500">
                        {result.duplicate
                          ? "Duplicate detected. "
                          : ""}

                        {result.message}
                      </td>

                    </tr>

                  ),
                )}

              </tbody>

            </table>

          </div>

        </div>
      ) : null}

    </div>
  );
}


function Metric({
  label,
  value,
}: {
  label: string;
  value: number;
}) {
  return (
    <div className="rounded-lg border border-slate-200 p-4">

      <div className="text-xs uppercase tracking-wide text-slate-400">
        {label}
      </div>

      <div className="mt-1 text-2xl font-semibold text-slate-950">
        {value}
      </div>

    </div>
  );
}