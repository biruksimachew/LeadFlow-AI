import {
  Filter,
  Search,
} from "lucide-react";

import Link from "next/link";

import { LeadStatusBadge } from "@/components/lead-status-badge";
import { getLeads } from "@/lib/data/leads";




type LeadsPageProps = {
  searchParams: Promise<{
    q?: string;
    status?: string;
    service?: string;
  }>;
};

const statuses = [
  "QUALIFIED_HOT",
  "QUALIFIED_WARM",
  "COLD",
  "REVIEW_REQUIRED",
  "DISQUALIFIED",
  "APPOINTMENT_BOOKED",
  "BOOKING_SENT",
];

const services = [
  "plumbing",
  "electrical",
  "hvac",
  "appliance_repair",
];

export default async function LeadsPage({
  searchParams,
}: LeadsPageProps) {
  const params = await searchParams;

  const search =
    params.q?.trim() ?? "";

  const status =
    params.status ?? "";

  const service =
    params.service ?? "";

  const leads = await getLeads({
    search,
    status,
    service,
  });

  return (
    <>
      <div className="flex flex-col justify-between gap-4 lg:flex-row lg:items-end">
        <div>
          <p className="text-sm font-medium text-slate-500">
            Operations
          </p>

          <h1 className="mt-1 text-3xl font-semibold tracking-tight text-slate-950">
            Leads
          </h1>

          <p className="mt-2 text-sm text-slate-600">
            Search, filter, and inspect
            leads moving through LeadFlow AI.
          </p>
        </div>

        <div className="text-sm text-slate-500">
          {leads.length} leads shown
        </div>
      </div>

      <form
        className="mt-8 grid gap-3 rounded-xl border border-slate-200 bg-white p-4 lg:grid-cols-[1fr_220px_220px_auto]"
      >
        <div className="relative">
          <Search className="absolute left-3 top-3.5 h-4 w-4 text-slate-400" />

          <input
            type="search"
            name="q"
            defaultValue={search}
            placeholder="Search name, email, phone, service..."
            className="w-full rounded-lg border border-slate-300 py-2.5 pl-10 pr-3 text-sm text-slate-950 outline-none focus:border-slate-900"
          />
        </div>

        <select
          name="status"
          defaultValue={status}
          className="rounded-lg border border-slate-300 bg-white px-3 py-2.5 text-sm text-slate-700 outline-none focus:border-slate-900"
        >
          <option value="">
            All statuses
          </option>

          {statuses.map(
            (item) => (
              <option
                key={item}
                value={item}
              >
                {item.replaceAll(
                  "_",
                  " ",
                )}
              </option>
            ),
          )}
        </select>

        <select
          name="service"
          defaultValue={service}
          className="rounded-lg border border-slate-300 bg-white px-3 py-2.5 text-sm text-slate-700 outline-none focus:border-slate-900"
        >
          <option value="">
            All services
          </option>

          {services.map(
            (item) => (
              <option
                key={item}
                value={item}
              >
                {item.replaceAll(
                  "_",
                  " ",
                )}
              </option>
            ),
          )}
        </select>

        <button
          type="submit"
          className="inline-flex items-center justify-center gap-2 rounded-lg bg-slate-950 px-5 py-2.5 text-sm font-medium text-white"
        >
          <Filter className="h-4 w-4" />
          Apply
        </button>
      </form>

      <div className="mt-6 overflow-hidden rounded-xl border border-slate-200 bg-white">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-slate-200">
            <thead className="bg-slate-50">
              <tr>
                {[
                  "Lead",
                  "Service",
                  "Location",
                  "Score",
                  "Status",
                  "Created",
                ].map(
                  (heading) => (
                    <th
                      key={heading}
                      className="px-5 py-3 text-left text-xs font-semibold uppercase tracking-wide text-slate-500"
                    >
                      {heading}
                    </th>
                  ),
                )}
              </tr>
            </thead>

            <tbody className="divide-y divide-slate-100">
              {leads.map(
                (lead) => (
                  <tr
                    key={lead.id}
                    className="transition hover:bg-slate-50"
                  >
                    <td className="px-5 py-4">
                      <Link
                        href={`/dashboard/leads/${lead.id}`}
                        className="font-medium text-slate-950 hover:underline"
                      >
                        {lead.full_name ??
                          "Unnamed lead"}
                      </Link>

                      <p className="mt-1 text-xs text-slate-500">
                        {lead.email_normalized ??
                          lead.phone_e164 ??
                          "No contact information"}
                      </p>
                    </td>

                    <td className="px-5 py-4 text-sm text-slate-700">
                      {formatLabel(
                        lead.service_type,
                      )}
                    </td>

                    <td className="px-5 py-4 text-sm text-slate-700">
                      {lead.location_text ??
                        "—"}
                    </td>

                    <td className="px-5 py-4">
                      <span className="text-sm font-semibold text-slate-950">
                        {lead.score ?? "—"}
                      </span>
                    </td>

                    <td className="px-5 py-4">
                      <LeadStatusBadge
                        status={
                          lead.status
                        }
                      />
                    </td>

                    <td className="whitespace-nowrap px-5 py-4 text-sm text-slate-500">
                      {formatDate(
                        lead.created_at,
                      )}
                    </td>
                  </tr>
                ),
              )}

              {leads.length === 0 ? (
                <tr>
                  <td
                    colSpan={6}
                    className="px-6 py-14 text-center text-sm text-slate-500"
                  >
                    No leads match these
                    filters.
                  </td>
                </tr>
              ) : null}
            </tbody>
          </table>
        </div>
      </div>
    </>
  );
}

function formatLabel(
  value: string | null,
) {
  if (!value) {
    return "—";
  }

  return value
    .replaceAll("_", " ")
    .replace(/\b\w/g, (character) =>
      character.toUpperCase(),
    );
}

function formatDate(
  value: string,
) {
  return new Intl.DateTimeFormat(
    "en-US",
    {
      dateStyle: "medium",
      timeStyle: "short",
    },
  ).format(new Date(value));
}