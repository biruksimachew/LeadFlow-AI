import {
  Activity,
  AlertTriangle,
  CalendarCheck,
  Clock3,
  Flame,
  ListChecks,
  MessageSquareWarning,
  Users,
} from "lucide-react";

import Link from "next/link";

import { LeadStatusBadge } from "@/components/lead-status-badge";
import {
  type DashboardBreakdownItem,
  getDashboardSnapshot,
} from "@/lib/data/dashboard";

export default async function DashboardPage() {
  const stats =
    await getDashboardSnapshot();

  const cards = [
    {
      label: "Total leads",
      value: stats.totalLeads,
      hint: "All canonical leads",
      icon: Users,
    },
    {
      label: "New in 24 hours",
      value: stats.newLeads24h,
      hint: "Recently accepted",
      icon: Activity,
    },
    {
      label: "Hot leads",
      value: stats.hotLeads,
      hint: "Priority follow-up",
      icon: Flame,
    },
    {
      label: "Review queue",
      value: stats.reviewRequired,
      hint: "Human decision required",
      icon: ListChecks,
    },
    {
      label: "Appointments booked",
      value: stats.appointmentsBooked,
      hint: "Confirmed appointments",
      icon: CalendarCheck,
    },
    {
      label: "Open workflow errors",
      value: stats.openWorkflowErrors,
      hint: `${stats.deadLetterWorkflowErrors} dead letter`,
      icon: AlertTriangle,
    },
  ];

  const signals: SystemSignal[] = [
    {
      label: "Lead intake",
      value: (
        stats.newLeads24h > 0
          ? `${stats.newLeads24h} accepted in 24h`
          : "No leads accepted in 24h"
      ),
      tone: (
        stats.newLeads24h > 0
          ? "healthy"
          : "neutral"
      ),
    },
    {
      label: "CRM synchronization",
      value: (
        stats.failedCrmSyncs > 0
          ? `${stats.failedCrmSyncs} failed syncs`
          : "No failed syncs"
      ),
      tone: (
        stats.failedCrmSyncs > 0
          ? "attention"
          : "healthy"
      ),
    },
    {
      label: "Communication engine",
      value: (
        stats.failedCommunications > 0
          ? `${stats.failedCommunications} failed messages`
          : "No failed messages"
      ),
      tone: (
        stats.failedCommunications > 0
          ? "attention"
          : "healthy"
      ),
    },
  ];

  return (
    <>
      <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-end">
        <div>
          <p className="text-sm font-medium text-slate-500">
            Operations overview
          </p>

          <h1 className="mt-1 text-3xl font-semibold tracking-tight text-slate-950">
            Dashboard
          </h1>

          <p className="mt-2 text-sm text-slate-600">
            Live lead, workflow, CRM, communication, and booking visibility.
          </p>
        </div>

        <p className="text-xs text-slate-500">
          Updated{" "}
          {formatDateTime(
            stats.generatedAt,
          )}
        </p>
      </div>

      <div className="mt-8 grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
        {cards.map(
          ({
            label,
            value,
            hint,
            icon: Icon,
          }) => (
            <div
              key={label}
              className="rounded-xl border border-slate-200 bg-white p-5"
            >
              <div className="flex items-start justify-between gap-4">
                <div>
                  <p className="text-sm font-medium text-slate-500">
                    {label}
                  </p>

                  <p className="mt-4 text-3xl font-semibold tracking-tight text-slate-950">
                    {value}
                  </p>

                  <p className="mt-2 text-xs text-slate-500">
                    {hint}
                  </p>
                </div>

                <Icon
                  aria-hidden="true"
                  className="h-5 w-5 text-slate-400"
                />
              </div>
            </div>
          ),
        )}
      </div>

      <section className="mt-8 rounded-xl border border-slate-200 bg-white p-6">
        <div className="flex flex-col justify-between gap-2 sm:flex-row sm:items-end">
          <div>
            <h2 className="text-lg font-semibold text-slate-950">
              Operational signals
            </h2>

            <p className="mt-1 text-sm text-slate-500">
              Database-backed signals rather than hardcoded service claims.
            </p>
          </div>

          {stats.latestLeadAt ? (
            <p className="text-xs text-slate-500">
              Latest lead{" "}
              {formatRelativeAge(
                stats.latestLeadAt,
              )}
            </p>
          ) : null}
        </div>

        <div className="mt-5 grid gap-4 sm:grid-cols-3">
          {signals.map(
            (signal) => (
              <SystemStatus
                key={signal.label}
                label={signal.label}
                value={signal.value}
                tone={signal.tone}
              />
            ),
          )}
        </div>
      </section>

      <div className="mt-8 grid gap-6 xl:grid-cols-2">
        <BreakdownPanel
          title="Pipeline status"
          description="Current canonical lead statuses."
          items={stats.statusBreakdown}
        />

        <BreakdownPanel
          title="Lead sources"
          description="Where accepted leads originated."
          items={stats.sourceBreakdown}
        />

        <BreakdownPanel
          title="Service mix"
          description="Requested NorthStar service categories."
          items={stats.serviceBreakdown}
        />

        <BreakdownPanel
          title="Score distribution"
          description="Deterministic score ranges, independent of hard-rule outcomes."
          items={stats.scoreBreakdown}
        />

        <BreakdownPanel
          title="Booking status"
          description="Appointment lifecycle records."
          items={stats.appointmentBreakdown}
        />

        <section className="rounded-xl border border-slate-200 bg-white p-6">
          <h2 className="text-lg font-semibold text-slate-950">
            Oldest items needing attention
          </h2>

          <p className="mt-1 text-sm text-slate-500">
            The longest-waiting review and unresolved workflow failure.
          </p>

          <div className="mt-5 space-y-4">
            {stats.oldestReview ? (
              <AttentionItem
                icon={Clock3}
                label="Human review"
                title={
                  stats.oldestReview
                    .fullName
                  ?? "Unnamed lead"
                }
                detail={`${formatLabel(
                  stats.oldestReview
                    .serviceType,
                )} · Score ${
                  stats.oldestReview
                    .score
                }`}
                age={formatRelativeAge(
                  stats.oldestReview
                    .createdAt,
                )}
                href={`/dashboard/leads/${stats.oldestReview.id}`}
              />
            ) : (
              <ClearItem label="Review queue is clear" />
            )}

            {stats.oldestWorkflowError ? (
              <AttentionItem
                icon={
                  MessageSquareWarning
                }
                label="Workflow failure"
                title={
                  stats.oldestWorkflowError
                    .errorCode
                }
                detail={`${formatLabel(
                  stats.oldestWorkflowError
                    .failedAction,
                )} · ${
                  stats.oldestWorkflowError
                    .provider
                  ?? "internal"
                }`}
                age={formatRelativeAge(
                  stats.oldestWorkflowError
                    .createdAt,
                )}
                href="/dashboard/errors"
              />
            ) : (
              <ClearItem label="Workflow error queue is clear" />
            )}
          </div>
        </section>
      </div>

      <section className="mt-8 overflow-hidden rounded-xl border border-slate-200 bg-white">
        <div className="flex flex-col justify-between gap-3 border-b border-slate-200 px-6 py-5 sm:flex-row sm:items-center">
          <div>
            <h2 className="text-lg font-semibold text-slate-950">
              Recent leads
            </h2>

            <p className="mt-1 text-sm text-slate-500">
              The eight newest canonical lead records.
            </p>
          </div>

          <Link
            href="/dashboard/leads"
            className="text-sm font-medium text-slate-700 underline underline-offset-4"
          >
            Open lead workspace
          </Link>
        </div>

        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-slate-200">
            <thead className="bg-slate-50">
              <tr>
                {[
                  "Lead",
                  "Source",
                  "Service",
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
              {stats.recentLeads.map(
                (lead) => (
                  <tr
                    key={lead.id}
                    className="hover:bg-slate-50"
                  >
                    <td className="px-5 py-4">
                      <Link
                        href={`/dashboard/leads/${lead.id}`}
                        className="font-medium text-slate-950 hover:underline"
                      >
                        {lead.fullName
                          ?? "Unnamed lead"}
                      </Link>

                      <p className="mt-1 text-xs text-slate-500">
                        {lead.email
                          ?? lead.correlationId
                          ?? "No reference"}
                      </p>
                    </td>

                    <td className="px-5 py-4 text-sm text-slate-700">
                      {formatLabel(
                        lead.source,
                      )}
                    </td>

                    <td className="px-5 py-4 text-sm text-slate-700">
                      {formatLabel(
                        lead.serviceType,
                      )}
                    </td>

                    <td className="px-5 py-4 text-sm font-semibold text-slate-950">
                      {lead.score}
                    </td>

                    <td className="px-5 py-4">
                      <LeadStatusBadge
                        status={lead.status}
                      />
                    </td>

                    <td className="whitespace-nowrap px-5 py-4 text-sm text-slate-500">
                      {formatDateTime(
                        lead.createdAt,
                      )}
                    </td>
                  </tr>
                ),
              )}

              {stats.recentLeads.length === 0 ? (
                <tr>
                  <td
                    colSpan={6}
                    className="px-6 py-14 text-center text-sm text-slate-500"
                  >
                    No leads have been created yet.
                  </td>
                </tr>
              ) : null}
            </tbody>
          </table>
        </div>
      </section>
    </>
  );
}

type SignalTone =
  | "healthy"
  | "attention"
  | "neutral";

type SystemSignal = {
  label: string;
  value: string;
  tone: SignalTone;
};

function SystemStatus({
  label,
  value,
  tone,
}: SystemSignal) {
  const dotClass = {
    healthy: "bg-emerald-500",
    attention: "bg-amber-500",
    neutral: "bg-slate-400",
  }[tone];

  return (
    <div className="rounded-lg bg-slate-50 p-4">
      <p className="text-sm text-slate-500">
        {label}
      </p>

      <div className="mt-2 flex items-center gap-2">
        <span
          aria-hidden="true"
          className={`h-2 w-2 rounded-full ${dotClass}`}
        />

        <span className="text-sm font-medium text-slate-900">
          {value}
        </span>
      </div>
    </div>
  );
}

function BreakdownPanel({
  title,
  description,
  items,
}: {
  title: string;
  description: string;
  items: DashboardBreakdownItem[];
}) {
  const visibleItems = items.filter(
    (item) => item.count > 0,
  );

  const displayedItems = (
    visibleItems.length > 0
      ? visibleItems
      : items.slice(0, 1)
  );

  const maximum = Math.max(
    ...displayedItems.map(
      (item) => item.count,
    ),
    1,
  );

  const total = items.reduce(
    (sum, item) =>
      sum + item.count,
    0,
  );

  return (
    <section className="rounded-xl border border-slate-200 bg-white p-6">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h2 className="text-lg font-semibold text-slate-950">
            {title}
          </h2>

          <p className="mt-1 text-sm text-slate-500">
            {description}
          </p>
        </div>

        <span className="text-sm font-semibold text-slate-700">
          {total}
        </span>
      </div>

      <div className="mt-5 space-y-4">
        {displayedItems.map(
          (item) => (
            <div key={item.key}>
              <div className="flex items-center justify-between gap-4 text-sm">
                <span className="text-slate-600">
                  {item.label}
                </span>

                <span className="font-medium text-slate-950">
                  {item.count}
                </span>
              </div>

              <div className="mt-2 h-2 overflow-hidden rounded-full bg-slate-100">
                <div
                  className="h-full rounded-full bg-slate-700"
                  style={{
                    width: `${Math.max(
                      item.count > 0
                        ? 8
                        : 0,
                      Math.round(
                        (
                          item.count
                          / maximum
                        ) * 100,
                      ),
                    )}%`,
                  }}
                />
              </div>
            </div>
          ),
        )}

        {total === 0 ? (
          <p className="text-sm text-slate-500">
            No data is available for this distribution.
          </p>
        ) : null}
      </div>
    </section>
  );
}

function AttentionItem({
  icon: Icon,
  label,
  title,
  detail,
  age,
  href,
}: {
  icon: typeof Clock3;
  label: string;
  title: string;
  detail: string;
  age: string;
  href: string;
}) {
  return (
    <Link
      href={href}
      className="block rounded-lg border border-slate-200 p-4 transition hover:bg-slate-50"
    >
      <div className="flex items-start gap-3">
        <Icon
          aria-hidden="true"
          className="mt-0.5 h-5 w-5 text-amber-600"
        />

        <div className="min-w-0">
          <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
            {label}
          </p>

          <p className="mt-1 truncate font-medium text-slate-950">
            {title}
          </p>

          <p className="mt-1 text-sm text-slate-500">
            {detail}
          </p>

          <p className="mt-2 text-xs font-medium text-amber-700">
            Waiting {age}
          </p>
        </div>
      </div>
    </Link>
  );
}

function ClearItem({
  label,
}: {
  label: string;
}) {
  return (
    <div className="rounded-lg border border-emerald-200 bg-emerald-50 p-4 text-sm font-medium text-emerald-800">
      {label}
    </div>
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

function formatDateTime(
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

function formatRelativeAge(
  value: string,
) {
  const timestamp =
    new Date(value).getTime();

  if (!Number.isFinite(timestamp)) {
    return "an unknown time";
  }

  const elapsed = Math.max(
    0,
    Date.now() - timestamp,
  );

  const minutes = Math.floor(
    elapsed / 60_000,
  );

  if (minutes < 1) {
    return "less than a minute";
  }

  if (minutes < 60) {
    return `${minutes}m`;
  }

  const hours = Math.floor(
    minutes / 60,
  );

  if (hours < 24) {
    return `${hours}h`;
  }

  const days = Math.floor(
    hours / 24,
  );

  return `${days}d`;
}
