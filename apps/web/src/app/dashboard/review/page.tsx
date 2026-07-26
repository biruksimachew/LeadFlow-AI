import {
  AlertCircle,
  ArrowRight,
  Clock3,
  MapPin,
  UserRound,
} from "lucide-react";

import Link from "next/link";

import {
  getReviewQueue,
  getReviewReason,
} from "@/lib/data/leads";

import { ReviewResolutionForm } from "./review-resolution-form";

export default async function ReviewPage() {
  const leads =
    await getReviewQueue();

  const reviewCases =
    await Promise.all(
      leads.map(async (lead) => ({
        lead,
        reason:
          await getReviewReason(
            lead.id,
          ),
      })),
    );

  return (
    <>
      <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-end">
        <div>
          <p className="text-sm font-medium text-slate-500">
            Human review
          </p>

          <h1 className="mt-1 text-3xl font-semibold tracking-tight text-slate-950">
            Review Queue
          </h1>

          <p className="mt-2 text-sm text-slate-600">
            Leads requiring a human
            decision before automation
            can continue.
          </p>
        </div>

        <div className="rounded-lg border border-slate-200 bg-white px-4 py-2">
          <span className="text-sm text-slate-500">
            Open cases
          </span>

          <span className="ml-3 text-lg font-semibold text-slate-950">
            {reviewCases.length}
          </span>
        </div>
      </div>

      {reviewCases.length > 0 ? (
        <div className="mt-8 space-y-4">
          {reviewCases.map(
            ({
              lead,
              reason,
            }) => (
              <article
                key={lead.id}
                className="rounded-xl border border-slate-200 bg-white p-6"
              >
                <div className="flex flex-col justify-between gap-5 xl:flex-row xl:items-start">
                  <div className="min-w-0 flex-1">
                    <div className="flex flex-wrap items-center gap-3">
                      <h2 className="text-lg font-semibold text-slate-950">
                        {lead.full_name ??
                          "Unnamed lead"}
                      </h2>

                      <span className="inline-flex rounded-full bg-purple-50 px-2.5 py-1 text-xs font-semibold text-purple-700 ring-1 ring-inset ring-purple-600/20">
                        Review Required
                      </span>
                    </div>

                    <p className="mt-1 break-all text-xs text-slate-400">
                      {
                        lead.correlation_id
                      }
                    </p>

                    <div className="mt-5 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
                      <Meta
                        icon={
                          UserRound
                        }
                        label="Service"
                        value={formatLabel(
                          lead.service_type,
                        )}
                      />

                      <Meta
                        icon={
                          AlertCircle
                        }
                        label="Score"
                        value={
                          lead.score !==
                          null
                            ? String(
                                lead.score,
                              )
                            : "—"
                        }
                      />

                      <Meta
                        icon={MapPin}
                        label="Location"
                        value={
                          lead.location_text ??
                          "—"
                        }
                      />

                      <Meta
                        icon={Clock3}
                        label="Waiting"
                        value={formatAge(
                          lead.created_at,
                        )}
                      />
                    </div>

                    <div className="mt-5 rounded-lg border border-amber-200 bg-amber-50 p-4">
                      <p className="text-xs font-semibold uppercase tracking-wide text-amber-700">
                        Review reason
                      </p>

                      <p className="mt-2 text-sm leading-6 text-amber-900">
                        {getReasonText(
                          reason,
                          lead.last_error_code,
                        )}
                      </p>

                      {reason?.provider ? (
                        <p className="mt-2 text-xs text-amber-700">
                          Provider:{" "}
                          {
                            reason.provider
                          }
                        </p>
                      ) : null}
                    </div>
                  </div>

                  <div className="flex shrink-0 flex-col gap-2 sm:flex-row xl:flex-col">
                    <Link
                      href={`/dashboard/leads/${lead.id}`}
                      className="inline-flex items-center justify-center gap-2 rounded-lg border border-slate-300 bg-white px-4 py-2.5 text-sm font-medium text-slate-700 transition hover:bg-slate-50"
                    >
                      Inspect lead

                      <ArrowRight className="h-4 w-4" />
                    </Link>

                    <ReviewResolutionForm
                      leadId={lead.id}
                    />

                  </div>
                </div>
              </article>
            ),
          )}
        </div>
      ) : (
        <div className="mt-8 rounded-xl border border-dashed border-slate-300 bg-white px-6 py-16 text-center">
          <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-emerald-50">
            <AlertCircle className="h-5 w-5 text-emerald-600" />
          </div>

          <h2 className="mt-4 text-lg font-semibold text-slate-950">
            Review queue is clear
          </h2>

          <p className="mx-auto mt-2 max-w-md text-sm leading-6 text-slate-500">
            No leads currently require
            human intervention.
          </p>
        </div>
      )}
    </>
  );
}


function Meta({
  icon: Icon,
  label,
  value,
}: {
  icon: React.ComponentType<{
    className?: string;
  }>;
  label: string;
  value: string;
}) {
  return (
    <div className="flex gap-3">
      <Icon className="mt-0.5 h-4 w-4 shrink-0 text-slate-400" />

      <div className="min-w-0">
        <p className="text-xs font-medium uppercase tracking-wide text-slate-400">
          {label}
        </p>

        <p className="mt-1 wrap-break-word text-sm font-medium text-slate-800">
          {value}
        </p>
      </div>
    </div>
  );
}


function getReasonText(
  event:
    | {
        event_type?: string | null;
        details?: unknown;
        error_code?: string | null;
        error_message?: string | null;
        provider?: string | null;
      }
    | null,
  leadError: string | null,
) {
  if (event?.error_message) {
    return event.error_message;
  }

  if (event?.error_code) {
    return formatLabel(
      event.error_code,
    );
  }

  if (leadError) {
    return formatLabel(leadError);
  }

  if (
    event?.details &&
    typeof event.details ===
      "object"
  ) {
    const details =
      event.details as Record<
        string,
        unknown
      >;

    const candidates = [
      details.reason,
      details.review_reason,
      details.explanation,
      details.message,
    ];

    const text =
      candidates.find(
        (value) =>
          typeof value === "string",
      );

    if (
      typeof text === "string"
    ) {
      return text;
    }
  }

  return "Lead requires human review before further automation.";
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


function formatAge(
  value: string,
) {
  const milliseconds =
    Date.now() -
    new Date(value).getTime();

  const minutes =
    Math.max(
      0,
      Math.floor(
        milliseconds / 60_000,
      ),
    );

  if (minutes < 60) {
    return `${minutes}m`;
  }

  const hours =
    Math.floor(
      minutes / 60,
    );

  if (hours < 24) {
    return `${hours}h`;
  }

  const days =
    Math.floor(
      hours / 24,
    );

  return `${days}d`;
}