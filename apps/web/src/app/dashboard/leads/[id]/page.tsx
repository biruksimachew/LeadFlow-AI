import type { ComponentType } from "react";

import {
  ArrowLeft,
  CalendarDays,
  Mail,
  MapPin,
  Phone,
  UserRound,
} from "lucide-react";

import Link from "next/link";
import { notFound } from "next/navigation";

import { LeadStatusBadge } from "@/components/lead-status-badge";

import {
  getLead,
  getLeadAppointments,
  getLeadCommunications,
  getLeadWorkflowEvents,
} from "@/lib/data/leads";


type LeadDetailPageProps = {
  params: Promise<{
    id: string;
  }>;
};


export default async function LeadDetailPage({
  params,
}: LeadDetailPageProps) {
  const { id } = await params;

  const lead = await getLead(id);

  if (!lead) {
    notFound();
  }

  const [
    workflowEvents,
    communications,
    appointments,
  ] = await Promise.all([
    getLeadWorkflowEvents(id),
    getLeadCommunications(id),
    getLeadAppointments(id),
  ]);

  return (
    <>
      <Link
        href="/dashboard/leads"
        className="inline-flex items-center gap-2 text-sm font-medium text-slate-500 transition hover:text-slate-950"
      >
        <ArrowLeft className="h-4 w-4" />

        Back to leads
      </Link>

      <div className="mt-6 flex flex-col justify-between gap-5 lg:flex-row lg:items-start">
        <div>
          <div className="flex flex-wrap items-center gap-3">
            <h1 className="text-3xl font-semibold tracking-tight text-slate-950">
              {lead.full_name ??
                "Unnamed lead"}
            </h1>

            <LeadStatusBadge
              status={lead.status}
            />
          </div>

          <p className="mt-2 text-sm text-slate-500">
            Correlation ID:{" "}
            {lead.correlation_id ??
              "—"}
          </p>
        </div>

        <div className="rounded-xl border border-slate-200 bg-white px-5 py-4">
          <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
            Qualification score
          </p>

          <p className="mt-1 text-3xl font-semibold text-slate-950">
            {lead.score ?? "—"}
          </p>
        </div>
      </div>

      <div className="mt-8 grid gap-6 xl:grid-cols-2">
        <section className="rounded-xl border border-slate-200 bg-white p-6">
          <h2 className="text-lg font-semibold text-slate-950">
            Lead information
          </h2>

          <div className="mt-6 grid gap-5 sm:grid-cols-2">
            <Detail
              icon={UserRound}
              label="Service"
              value={formatLabel(
                lead.service_type,
              )}
            />

            <Detail
              icon={CalendarDays}
              label="Urgency"
              value={formatLabel(
                lead.urgency,
              )}
            />

            <Detail
              icon={Mail}
              label="Email"
              value={
                lead.email_normalized
              }
            />

            <Detail
              icon={Phone}
              label="Phone"
              value={lead.phone_e164}
            />

            <Detail
              icon={MapPin}
              label="Location"
              value={
                lead.location_text
              }
            />

            <Detail
              icon={MapPin}
              label="Service zone"
              value={
                lead.service_zone
              }
            />
          </div>
        </section>

        <section className="rounded-xl border border-slate-200 bg-white p-6">
          <h2 className="text-lg font-semibold text-slate-950">
            Automation state
          </h2>

          <dl className="mt-5 divide-y divide-slate-100">
            <Row
              label="Assigned owner"
              value={
                lead.assigned_owner_id
              }
            />

            <Row
              label="HubSpot contact"
              value={
                lead.hubspot_contact_id
              }
            />

            <Row
              label="HubSpot deal"
              value={
                lead.hubspot_deal_id
              }
            />

            <Row
              label="Appointment"
              value={formatLabel(
                lead.appointment_status,
              )}
            />

            <Row
              label="Last error"
              value={
                lead.last_error_code
              }
            />

            <Row
              label="Created"
              value={formatDate(
                lead.created_at,
              )}
            />

            <Row
              label="Updated"
              value={formatDate(
                lead.updated_at,
              )}
            />
          </dl>
        </section>
      </div>

      <div className="mt-6 grid gap-6 xl:grid-cols-[1.5fr_1fr]">

        {/* WORKFLOW TIMELINE */}

        <section className="rounded-xl border border-slate-200 bg-white p-6">
          <div>
            <h2 className="text-lg font-semibold text-slate-950">
              Workflow timeline
            </h2>

            <p className="mt-1 text-sm text-slate-500">
              Append-only processing
              history for this lead.
            </p>
          </div>

          <div className="mt-7">
            {workflowEvents.length > 0 ? (
              <div>
                {workflowEvents.map(
                  (event) => (
                    <div
                      key={event.id}
                      className="relative border-l border-slate-200 pb-8 pl-6 last:pb-0"
                    >
                      <span
                        className={[
                          "absolute -left-1.5 top-1 h-3 w-3 rounded-full border-2 border-white",
                          getEventDotStyle(
                            event.result,
                          ),
                        ].join(" ")}
                      />

                      <div className="flex flex-col justify-between gap-3 sm:flex-row sm:items-start">
                        <div>
                          <div className="flex flex-wrap items-center gap-2">
                            <p className="text-sm font-semibold text-slate-950">
                              {formatLabel(
                                event.event_type,
                              )}
                            </p>

                            <ResultBadge
                              result={
                                event.result
                              }
                            />
                          </div>

                          <div className="mt-1 flex flex-wrap gap-x-4 gap-y-1 text-xs text-slate-500">
                            {event.provider ? (
                              <span>
                                Provider:{" "}
                                <strong className="font-medium text-slate-700">
                                  {
                                    event.provider
                                  }
                                </strong>
                              </span>
                            ) : null}

                            {event.actor_type ? (
                              <span>
                                Actor:{" "}
                                <strong className="font-medium text-slate-700">
                                  {formatLabel(
                                    event.actor_type,
                                  )}
                                </strong>
                              </span>
                            ) : null}

                            {event.actor_id ? (
                              <span>
                                Actor ID:{" "}
                                <strong className="font-medium text-slate-700">
                                  {
                                    event.actor_id
                                  }
                                </strong>
                              </span>
                            ) : null}
                          </div>
                        </div>

                        <time className="whitespace-nowrap text-xs text-slate-400">
                          {formatDate(
                            event.created_at,
                          )}
                        </time>
                      </div>

                      {event.details &&
                      Object.keys(
                        event.details,
                      ).length > 0 ? (
                        <div className="mt-3 rounded-lg border border-slate-200 bg-slate-50 p-3">
                          <div className="grid gap-3 sm:grid-cols-2">
                            {Object.entries(
                              event.details,
                            ).map(
                              ([
                                key,
                                value,
                              ]) => (
                                <div
                                  key={
                                    key
                                  }
                                  className="min-w-0"
                                >
                                  <p className="text-[11px] font-semibold uppercase tracking-wide text-slate-400">
                                    {formatLabel(
                                      key,
                                    )}
                                  </p>

                                  <p className="mt-1 wrap-break-word text-xs leading-5 text-slate-700">
                                    {formatDetailValue(
                                      value,
                                    )}
                                  </p>
                                </div>
                              ),
                            )}
                          </div>
                        </div>
                      ) : null}

                      {event.error_code ||
                      event.error_message ? (
                        <div className="mt-3 rounded-lg border border-red-200 bg-red-50 p-3">
                          {event.error_code ? (
                            <p className="text-xs font-semibold text-red-700">
                              {
                                event.error_code
                              }
                            </p>
                          ) : null}

                          {event.error_message ? (
                            <p className="mt-1 text-xs leading-5 text-red-700">
                              {
                                event.error_message
                              }
                            </p>
                          ) : null}
                        </div>
                      ) : null}
                    </div>
                  ),
                )}
              </div>
            ) : (
              <p className="text-sm text-slate-500">
                No workflow events found.
              </p>
            )}
          </div>
        </section>

        <div className="space-y-6">

          {/* COMMUNICATIONS */}

          <section className="rounded-xl border border-slate-200 bg-white p-6">
            <div>
              <h2 className="text-lg font-semibold text-slate-950">
                Communications
              </h2>

              <p className="mt-1 text-sm text-slate-500">
                Automated messages and
                notifications.
              </p>
            </div>

            <div className="mt-5 space-y-3">
              {communications.map(
                (communication) => (
                  <div
                    key={
                      communication.id
                    }
                    className="rounded-lg border border-slate-200 p-4"
                  >
                    <div className="flex items-center justify-between gap-3">
                      <p className="text-sm font-semibold text-slate-950">
                        {formatLabel(
                          communication.channel,
                        )}
                      </p>

                      <span className="text-xs font-medium text-slate-500">
                        {formatLabel(
                          communication.status,
                        )}
                      </span>
                    </div>

                    <p className="mt-2 text-xs text-slate-500">
                      Template:{" "}
                      {communication.template_key ??
                        "—"}
                    </p>

                    {communication.provider ? (
                      <p className="mt-1 text-xs text-slate-500">
                        Provider:{" "}
                        {
                          communication.provider
                        }
                      </p>
                    ) : null}

                    <p className="mt-2 text-xs text-slate-400">
                      {formatDate(
                        communication.created_at,
                      )}
                    </p>
                  </div>
                ),
              )}

              {communications.length ===
              0 ? (
                <p className="text-sm text-slate-500">
                  No communications found.
                </p>
              ) : null}
            </div>
          </section>

          {/* APPOINTMENTS */}

          <section className="rounded-xl border border-slate-200 bg-white p-6">
            <div>
              <h2 className="text-lg font-semibold text-slate-950">
                Appointments
              </h2>

              <p className="mt-1 text-sm text-slate-500">
                Booking activity for this
                lead.
              </p>
            </div>

            <div className="mt-5 space-y-3">
              {appointments.map(
                (appointment) => (
                  <div
                    key={appointment.id}
                    className="rounded-lg border border-slate-200 p-4"
                  >
                    <div className="flex items-center justify-between">
                      <p className="text-sm font-semibold text-slate-950">
                        {formatLabel(
                          appointment.status,
                        )}
                      </p>
                    </div>

                    {appointment.start_at ? (
                      <p className="mt-3 text-sm font-medium text-slate-700">
                        {formatDate(
                          appointment.start_at,
                        )}
                      </p>
                    ) : null}

                    {appointment.end_at ? (
                      <p className="mt-1 text-xs text-slate-500">
                        Ends:{" "}
                        {formatDate(
                          appointment.end_at,
                        )}
                      </p>
                    ) : null}

                    {appointment.timezone ? (
                      <p className="mt-2 text-xs text-slate-500">
                        {
                          appointment.timezone
                        }
                      </p>
                    ) : null}

                    {appointment.attendee_email ? (
                      <p className="mt-2 break-all text-xs text-slate-500">
                        {
                          appointment.attendee_email
                        }
                      </p>
                    ) : null}

                    {appointment.external_appointment_id ? (
                      <p className="mt-2 break-all text-xs text-slate-400">
                        Ref:{" "}
                        {
                          appointment.external_appointment_id
                        }
                      </p>
                    ) : null}
                  </div>
                ),
              )}

              {appointments.length ===
              0 ? (
                <p className="text-sm text-slate-500">
                  No appointment activity.
                </p>
              ) : null}
            </div>
          </section>
        </div>
      </div>
    </>
  );
}


function Detail({
  icon: Icon,
  label,
  value,
}: {
  icon: ComponentType<{
    className?: string;
  }>;
  label: string;
  value: string | null;
}) {
  return (
    <div className="flex gap-3">
      <Icon className="mt-0.5 h-4 w-4 shrink-0 text-slate-400" />

      <div className="min-w-0">
        <p className="text-xs font-medium uppercase tracking-wide text-slate-400">
          {label}
        </p>

        <p className="mt-1 wrap-break-word text-sm font-medium text-slate-800">
          {value || "—"}
        </p>
      </div>
    </div>
  );
}


function Row({
  label,
  value,
}: {
  label: string;
  value: string | null;
}) {
  return (
    <div className="flex items-start justify-between gap-6 py-3 first:pt-0 last:pb-0">
      <dt className="text-sm text-slate-500">
        {label}
      </dt>

      <dd className="max-w-[60%] break-all text-right text-sm font-medium text-slate-900">
        {value || "—"}
      </dd>
    </div>
  );
}


function ResultBadge({
  result,
}: {
  result: string | null;
}) {
  if (!result) {
    return null;
  }

  const styles: Record<
    string,
    string
  > = {
    succeeded:
      "bg-emerald-50 text-emerald-700 ring-emerald-600/20",

    failed:
      "bg-red-50 text-red-700 ring-red-600/20",

    skipped:
      "bg-slate-100 text-slate-600 ring-slate-500/20",

    pending:
      "bg-amber-50 text-amber-700 ring-amber-600/20",
  };

  const style =
    styles[result.toLowerCase()] ??
    "bg-slate-100 text-slate-600 ring-slate-500/20";

  return (
    <span
      className={[
        "inline-flex rounded-full px-2 py-0.5 text-[11px] font-semibold ring-1 ring-inset",
        style,
      ].join(" ")}
    >
      {formatLabel(result)}
    </span>
  );
}


function getEventDotStyle(
  result: string | null,
) {
  switch (result?.toLowerCase()) {
    case "succeeded":
      return "bg-emerald-500";

    case "failed":
      return "bg-red-500";

    case "skipped":
      return "bg-slate-400";

    case "pending":
      return "bg-amber-500";

    default:
      return "bg-slate-900";
  }
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


function formatDetailValue(
  value: unknown,
): string {
  if (
    value === null ||
    value === undefined
  ) {
    return "—";
  }

  if (typeof value === "string") {
    return value;
  }

  if (
    typeof value === "number" ||
    typeof value === "boolean"
  ) {
    return String(value);
  }

  try {
    return JSON.stringify(value);
  } catch {
    return String(value);
  }
}