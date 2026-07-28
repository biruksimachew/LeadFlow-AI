import { createClient } from "@/lib/supabase/server";

export type DashboardBreakdownItem = {
  key: string;
  label: string;
  count: number;
};

export type DashboardRecentLead = {
  id: string;
  correlationId: string | null;
  fullName: string | null;
  email: string | null;
  serviceType: string | null;
  source: string | null;
  score: number;
  status: string;
  createdAt: string;
};

export type DashboardAttentionLead = {
  id: string;
  correlationId: string | null;
  fullName: string | null;
  serviceType: string | null;
  score: number;
  status: string;
  createdAt: string;
};

export type DashboardAttentionError = {
  id: string;
  leadId: string;
  correlationId: string;
  failedAction: string;
  provider: string | null;
  errorCode: string;
  status: string;
  retryCount: number;
  createdAt: string;
};

export type DashboardSnapshot = {
  generatedAt: string;
  latestLeadAt: string | null;

  totalLeads: number;
  newLeads24h: number;

  hotLeads: number;
  warmLeads: number;
  coldLeads: number;
  reviewRequired: number;
  disqualifiedLeads: number;

  appointmentsBooked: number;
  openWorkflowErrors: number;
  deadLetterWorkflowErrors: number;
  failedCrmSyncs: number;
  failedCommunications: number;

  statusBreakdown: DashboardBreakdownItem[];
  sourceBreakdown: DashboardBreakdownItem[];
  serviceBreakdown: DashboardBreakdownItem[];
  scoreBreakdown: DashboardBreakdownItem[];
  appointmentBreakdown: DashboardBreakdownItem[];

  recentLeads: DashboardRecentLead[];
  oldestReview: DashboardAttentionLead | null;
  oldestWorkflowError: DashboardAttentionError | null;
};

type JsonRecord = Record<string, unknown>;

const statusLabels: Array<[string, string]> = [
  ["RECEIVED", "Received"],
  ["QUALIFIED_HOT", "Qualified hot"],
  ["QUALIFIED_WARM", "Qualified warm"],
  ["COLD", "Cold"],
  ["REVIEW_REQUIRED", "Review required"],
  ["DISQUALIFIED", "Disqualified"],
  ["BOOKING_SENT", "Booking sent"],
  ["APPOINTMENT_BOOKED", "Appointment booked"],
  ["CONTACTED", "Contacted"],
  ["CLOSED_WON", "Closed won"],
  ["CLOSED_LOST", "Closed lost"],
  ["DUPLICATE", "Duplicate"],
  ["INVALID", "Invalid"],
];

const sourceLabels: Array<[string, string]> = [
  ["website", "Website"],
  ["meta", "Meta"],
  ["manual", "Manual"],
  ["csv_test", "CSV test"],
];

const serviceLabels: Array<[string, string]> = [
  ["electrical", "Electrical"],
  ["plumbing", "Plumbing"],
  ["hvac", "HVAC"],
  ["appliance_repair", "Appliance repair"],
  ["other", "Other"],
];

const appointmentLabels: Array<[string, string]> = [
  ["LINK_SENT", "Link sent"],
  ["BOOKED", "Booked"],
  ["CANCELLED", "Cancelled"],
  ["COMPLETED", "Completed"],
];

function asRecord(
  value: unknown,
): JsonRecord {
  return (
    value
    && typeof value === "object"
    && !Array.isArray(value)
      ? value as JsonRecord
      : {}
  );
}

function asArray(
  value: unknown,
): unknown[] {
  return Array.isArray(value)
    ? value
    : [];
}

function asString(
  value: unknown,
): string {
  return typeof value === "string"
    ? value
    : "";
}

function asNullableString(
  value: unknown,
): string | null {
  return typeof value === "string"
    ? value
    : null;
}

function asNumber(
  value: unknown,
): number {
  if (
    typeof value === "number"
    && Number.isFinite(value)
  ) {
    return value;
  }

  if (
    typeof value === "string"
    && value.trim() !== ""
  ) {
    const parsed = Number(value);

    if (Number.isFinite(parsed)) {
      return parsed;
    }
  }

  return 0;
}

function breakdown(
  value: unknown,
  labels: Array<[string, string]>,
): DashboardBreakdownItem[] {
  const record = asRecord(value);

  return labels.map(
    ([key, label]) => ({
      key,
      label,
      count: asNumber(record[key]),
    }),
  );
}

function recentLead(
  value: unknown,
): DashboardRecentLead | null {
  const row = asRecord(value);
  const id = asString(row.id);
  const status = asString(row.status);
  const createdAt = asString(
    row.created_at,
  );

  if (!id || !status || !createdAt) {
    return null;
  }

  return {
    id,
    correlationId:
      asNullableString(
        row.correlation_id,
      ),
    fullName:
      asNullableString(row.full_name),
    email:
      asNullableString(
        row.email_normalized,
      ),
    serviceType:
      asNullableString(
        row.service_type,
      ),
    source:
      asNullableString(row.source),
    score: asNumber(row.score),
    status,
    createdAt,
  };
}

function attentionLead(
  value: unknown,
): DashboardAttentionLead | null {
  const row = asRecord(value);
  const id = asString(row.id);
  const status = asString(row.status);
  const createdAt = asString(
    row.created_at,
  );

  if (!id || !status || !createdAt) {
    return null;
  }

  return {
    id,
    correlationId:
      asNullableString(
        row.correlation_id,
      ),
    fullName:
      asNullableString(row.full_name),
    serviceType:
      asNullableString(
        row.service_type,
      ),
    score: asNumber(row.score),
    status,
    createdAt,
  };
}

function attentionError(
  value: unknown,
): DashboardAttentionError | null {
  const row = asRecord(value);
  const id = asString(row.id);
  const leadId = asString(row.lead_id);
  const correlationId = asString(
    row.correlation_id,
  );
  const failedAction = asString(
    row.failed_action,
  );
  const errorCode = asString(
    row.error_code,
  );
  const status = asString(row.status);
  const createdAt = asString(
    row.created_at,
  );

  if (
    !id
    || !leadId
    || !correlationId
    || !failedAction
    || !errorCode
    || !status
    || !createdAt
  ) {
    return null;
  }

  return {
    id,
    leadId,
    correlationId,
    failedAction,
    provider:
      asNullableString(row.provider),
    errorCode,
    status,
    retryCount:
      asNumber(row.retry_count),
    createdAt,
  };
}

export async function getDashboardSnapshot():
  Promise<DashboardSnapshot> {
  const supabase = await createClient();

  const {
    data,
    error,
  } = await supabase.rpc(
    "get_leadflow_dashboard_snapshot",
  );

  if (error) {
    throw new Error(
      `Unable to load dashboard: ${error.message}`,
    );
  }

  const snapshot = asRecord(data);
  const statuses = asRecord(
    snapshot.status_breakdown,
  );
  const appointments = asRecord(
    snapshot.appointment_breakdown,
  );
  const scores = asRecord(
    snapshot.score_breakdown,
  );

  return {
    generatedAt:
      asString(snapshot.generated_at)
      || new Date().toISOString(),

    latestLeadAt:
      asNullableString(
        snapshot.latest_lead_at,
      ),

    totalLeads:
      asNumber(snapshot.total_leads),

    newLeads24h:
      asNumber(
        snapshot.new_leads_24h,
      ),

    hotLeads:
      asNumber(
        statuses.QUALIFIED_HOT,
      ),

    warmLeads:
      asNumber(
        statuses.QUALIFIED_WARM,
      ),

    coldLeads:
      asNumber(statuses.COLD),

    reviewRequired:
      asNumber(
        statuses.REVIEW_REQUIRED,
      ),

    disqualifiedLeads:
      asNumber(
        statuses.DISQUALIFIED,
      ),

    appointmentsBooked:
      asNumber(appointments.BOOKED),

    openWorkflowErrors:
      asNumber(
        snapshot.open_workflow_errors,
      ),

    deadLetterWorkflowErrors:
      asNumber(
        snapshot.dead_letter_workflow_errors,
      ),

    failedCrmSyncs:
      asNumber(
        snapshot.failed_crm_syncs,
      ),

    failedCommunications:
      asNumber(
        snapshot.failed_communications,
      ),

    statusBreakdown: breakdown(
      statuses,
      statusLabels,
    ),

    sourceBreakdown: breakdown(
      snapshot.source_breakdown,
      sourceLabels,
    ),

    serviceBreakdown: breakdown(
      snapshot.service_breakdown,
      serviceLabels,
    ),

    scoreBreakdown: [
      {
        key: "high",
        label: "80–100",
        count: asNumber(scores.high),
      },
      {
        key: "medium",
        label: "55–79",
        count: asNumber(scores.medium),
      },
      {
        key: "low",
        label: "0–54",
        count: asNumber(scores.low),
      },
    ],

    appointmentBreakdown: breakdown(
      appointments,
      appointmentLabels,
    ),

    recentLeads: asArray(
      snapshot.recent_leads,
    )
      .map(recentLead)
      .filter(
        (
          item,
        ): item is DashboardRecentLead =>
          item !== null,
      ),

    oldestReview: attentionLead(
      snapshot.oldest_review,
    ),

    oldestWorkflowError:
      attentionError(
        snapshot.oldest_workflow_error,
      ),
  };
}
