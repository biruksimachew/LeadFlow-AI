import {
  Filter,
  Search,
  X,
} from "lucide-react";

import Link from "next/link";

import { LeadStatusBadge } from "@/components/lead-status-badge";
import {
  getLeadOwners,
  getLeads,
} from "@/lib/data/leads";

type LeadsPageProps = {
  searchParams: Promise<{
    q?: string;
    status?: string;
    service?: string;
    source?: string;
    score?: string;
    owner?: string;
    from?: string;
    to?: string;
    sort?: string;
    page?: string;
  }>;
};

const statuses = [
  "RECEIVED",
  "QUALIFIED_HOT",
  "QUALIFIED_WARM",
  "COLD",
  "REVIEW_REQUIRED",
  "DISQUALIFIED",
  "BOOKING_SENT",
  "APPOINTMENT_BOOKED",
  "CONTACTED",
  "CLOSED_WON",
  "CLOSED_LOST",
  "DUPLICATE",
  "INVALID",
];

const services = [
  "plumbing",
  "electrical",
  "hvac",
  "appliance_repair",
  "other",
];

const sources = [
  "website",
  "meta",
  "manual",
  "csv_test",
];

const scoreBands = [
  ["high", "80–100"],
  ["medium", "55–79"],
  ["low", "0–54"],
] as const;

const sortOptions = [
  ["newest", "Newest first"],
  ["oldest", "Oldest first"],
  ["score_desc", "Highest score"],
  ["score_asc", "Lowest score"],
  [
    "updated_desc",
    "Recently updated",
  ],
] as const;

export default async function LeadsPage({
  searchParams,
}: LeadsPageProps) {
  const params = await searchParams;

  const filters = {
    search:
      params.q?.trim() ?? "",

    status:
      params.status ?? "",

    service:
      params.service ?? "",

    source:
      params.source ?? "",

    scoreBand:
      params.score ?? "",

    owner:
      params.owner ?? "",

    createdFrom:
      params.from ?? "",

    createdTo:
      params.to ?? "",

    sort:
      params.sort ?? "newest",

    page: pageNumber(
      params.page,
    ),
  };

  const [
    result,
    owners,
  ] = await Promise.all([
    getLeads(filters),
    getLeadOwners(),
  ]);

  const firstShown = (
    result.totalCount === 0
      ? 0
      : (
        (result.page - 1)
        * result.pageSize
      ) + 1
  );

  const lastShown = Math.min(
    result.page
      * result.pageSize,
    result.totalCount,
  );

  const hasFilters = Boolean(
    filters.search
    || filters.status
    || filters.service
    || filters.source
    || filters.scoreBand
    || filters.owner
    || filters.createdFrom
    || filters.createdTo
    || filters.sort !== "newest",
  );

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
            Search, filter, sort, and inspect canonical leads moving through LeadFlow AI.
          </p>
        </div>

        <div className="text-sm text-slate-500">
          Showing {firstShown}–{lastShown} of{" "}
          {result.totalCount}
        </div>
      </div>

      <form
        method="get"
        className="mt-8 rounded-xl border border-slate-200 bg-white p-4"
      >
        <div className="grid gap-4 lg:grid-cols-2">
          <label className="text-sm font-medium text-slate-700">
            Search

            <div className="relative mt-2">
              <Search
                aria-hidden="true"
                className="absolute left-3 top-3.5 h-4 w-4 text-slate-400"
              />

              <input
                type="search"
                name="q"
                defaultValue={
                  filters.search
                }
                placeholder="Name, email, phone, correlation ID..."
                className="w-full rounded-lg border border-slate-300 py-2.5 pl-10 pr-3 text-sm text-slate-950 outline-none focus:border-slate-900"
              />
            </div>
          </label>

          <FilterSelect
            label="Status"
            name="status"
            value={filters.status}
            emptyLabel="All statuses"
            options={statuses.map(
              (item) => [
                item,
                formatLabel(item),
              ],
            )}
          />
        </div>

        <div className="mt-4 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          <FilterSelect
            label="Service"
            name="service"
            value={filters.service}
            emptyLabel="All services"
            options={services.map(
              (item) => [
                item,
                formatLabel(item),
              ],
            )}
          />

          <FilterSelect
            label="Source"
            name="source"
            value={filters.source}
            emptyLabel="All sources"
            options={sources.map(
              (item) => [
                item,
                formatLabel(item),
              ],
            )}
          />

          <FilterSelect
            label="Score range"
            name="score"
            value={filters.scoreBand}
            emptyLabel="All scores"
            options={[
              ...scoreBands,
            ]}
          />

          <FilterSelect
            label="Owner"
            name="owner"
            value={filters.owner}
            emptyLabel="All owners"
            options={[
              [
                "unassigned",
                "Unassigned",
              ],
              ...owners.map(
                (owner) => [
                  owner,
                  owner,
                ] as const,
              ),
            ]}
          />

          <DateFilter
            label="Created from"
            name="from"
            value={filters.createdFrom}
          />

          <DateFilter
            label="Created to"
            name="to"
            value={filters.createdTo}
          />

          <FilterSelect
            label="Sort"
            name="sort"
            value={filters.sort}
            emptyLabel="Newest first"
            options={[
              ...sortOptions,
            ]}
          />
        </div>

        <div className="mt-5 flex flex-wrap items-center gap-3">
          <button
            type="submit"
            className="inline-flex items-center justify-center gap-2 rounded-lg bg-slate-950 px-5 py-2.5 text-sm font-medium text-white"
          >
            <Filter
              aria-hidden="true"
              className="h-4 w-4"
            />
            Apply filters
          </button>

          {hasFilters ? (
            <Link
              href="/dashboard/leads"
              className="inline-flex items-center justify-center gap-2 rounded-lg border border-slate-300 bg-white px-5 py-2.5 text-sm font-medium text-slate-700 hover:bg-slate-50"
            >
              <X
                aria-hidden="true"
                className="h-4 w-4"
              />
              Clear filters
            </Link>
          ) : null}
        </div>
      </form>

      <div className="mt-6 overflow-hidden rounded-xl border border-slate-200 bg-white">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-slate-200">
            <thead className="bg-slate-50">
              <tr>
                {[
                  "Lead",
                  "Source",
                  "Service",
                  "Owner",
                  "Score",
                  "Status",
                  "Created",
                ].map(
                  (heading) => (
                    <th
                      key={heading}
                      scope="col"
                      className="px-5 py-3 text-left text-xs font-semibold uppercase tracking-wide text-slate-500"
                    >
                      {heading}
                    </th>
                  ),
                )}
              </tr>
            </thead>

            <tbody className="divide-y divide-slate-100">
              {result.items.map(
                (lead) => (
                  <tr
                    key={lead.id}
                    className="transition hover:bg-slate-50"
                  >
                    <td className="max-w-xs px-5 py-4">
                      <Link
                        href={`/dashboard/leads/${lead.id}`}
                        className="font-medium text-slate-950 hover:underline"
                      >
                        {lead.full_name
                          ?? "Unnamed lead"}
                      </Link>

                      <p className="mt-1 truncate text-xs text-slate-500">
                        {lead.email_normalized
                          ?? lead.phone_e164
                          ?? "No contact information"}
                      </p>

                      {lead.correlation_id ? (
                        <p
                          title={
                            lead.correlation_id
                          }
                          className="mt-1 truncate font-mono text-[11px] text-slate-400"
                        >
                          {lead.correlation_id}
                        </p>
                      ) : null}
                    </td>

                    <td className="px-5 py-4 text-sm text-slate-700">
                      {formatLabel(
                        lead.source,
                      )}
                    </td>

                    <td className="px-5 py-4 text-sm text-slate-700">
                      {formatLabel(
                        lead.service_type,
                      )}
                    </td>

                    <td className="max-w-40 px-5 py-4">
                      <span
                        title={
                          lead.assigned_owner_id
                          ?? undefined
                        }
                        className="block truncate font-mono text-xs text-slate-600"
                      >
                        {lead.assigned_owner_id
                          ?? "Unassigned"}
                      </span>
                    </td>

                    <td className="px-5 py-4">
                      <span className="text-sm font-semibold text-slate-950">
                        {lead.score ?? "—"}
                      </span>
                    </td>

                    <td className="px-5 py-4">
                      <LeadStatusBadge
                        status={lead.status}
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

              {result.items.length === 0 ? (
                <tr>
                  <td
                    colSpan={7}
                    className="px-6 py-14 text-center text-sm text-slate-500"
                  >
                    No leads match these filters.
                  </td>
                </tr>
              ) : null}
            </tbody>
          </table>
        </div>

        <Pagination
          page={result.page}
          totalPages={
            result.totalPages
          }
          params={params}
        />
      </div>
    </>
  );
}

function FilterSelect({
  label,
  name,
  value,
  emptyLabel,
  options,
}: {
  label: string;
  name: string;
  value: string;
  emptyLabel: string;
  options: ReadonlyArray<
    readonly [string, string]
  >;
}) {
  return (
    <label className="text-sm font-medium text-slate-700">
      {label}

      <select
        name={name}
        defaultValue={value}
        className="mt-2 w-full rounded-lg border border-slate-300 bg-white px-3 py-2.5 text-sm text-slate-700 outline-none focus:border-slate-900"
      >
        <option value="">
          {emptyLabel}
        </option>

        {options.map(
          ([optionValue, text]) => (
            <option
              key={optionValue}
              value={optionValue}
            >
              {text}
            </option>
          ),
        )}
      </select>
    </label>
  );
}

function DateFilter({
  label,
  name,
  value,
}: {
  label: string;
  name: string;
  value: string;
}) {
  return (
    <label className="text-sm font-medium text-slate-700">
      {label}

      <input
        type="date"
        name={name}
        defaultValue={value}
        className="mt-2 w-full rounded-lg border border-slate-300 bg-white px-3 py-2.5 text-sm text-slate-700 outline-none focus:border-slate-900"
      />
    </label>
  );
}

function Pagination({
  page,
  totalPages,
  params,
}: {
  page: number;
  totalPages: number;
  params: Awaited<
    LeadsPageProps[
      "searchParams"
    ]
  >;
}) {
  return (
    <nav
      aria-label="Lead list pagination"
      className="flex flex-col justify-between gap-3 border-t border-slate-200 px-5 py-4 sm:flex-row sm:items-center"
    >
      <p className="text-sm text-slate-500">
        Page {page} of {totalPages}
      </p>

      <div className="flex items-center gap-2">
        {page > 1 ? (
          <Link
            href={pageHref(
              params,
              page - 1,
            )}
            className="rounded-lg border border-slate-300 bg-white px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
          >
            Previous
          </Link>
        ) : (
          <span className="cursor-not-allowed rounded-lg border border-slate-200 bg-slate-50 px-4 py-2 text-sm font-medium text-slate-400">
            Previous
          </span>
        )}

        {page < totalPages ? (
          <Link
            href={pageHref(
              params,
              page + 1,
            )}
            className="rounded-lg border border-slate-300 bg-white px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
          >
            Next
          </Link>
        ) : (
          <span className="cursor-not-allowed rounded-lg border border-slate-200 bg-slate-50 px-4 py-2 text-sm font-medium text-slate-400">
            Next
          </span>
        )}
      </div>
    </nav>
  );
}

function pageHref(
  params: Awaited<
    LeadsPageProps[
      "searchParams"
    ]
  >,
  page: number,
) {
  const next =
    new URLSearchParams();

  Object.entries(params).forEach(
    ([key, value]) => {
      if (
        key !== "page"
        && typeof value === "string"
        && value.length > 0
      ) {
        next.set(key, value);
      }
    },
  );

  next.set(
    "page",
    String(page),
  );

  return `/dashboard/leads?${next.toString()}`;
}

function pageNumber(
  value: string | undefined,
) {
  const parsed = Number.parseInt(
    value ?? "1",
    10,
  );

  return (
    Number.isInteger(parsed)
    && parsed > 0
      ? parsed
      : 1
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
