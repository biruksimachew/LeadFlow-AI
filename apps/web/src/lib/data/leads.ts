import { createClient } from "@/lib/supabase/server";

export type LeadListItem = {
  id: string;
  correlation_id: string | null;
  source: string | null;
  full_name: string | null;
  email_normalized: string | null;
  phone_e164: string | null;
  service_type: string | null;
  location_text: string | null;
  service_zone: string | null;
  urgency: string | null;
  score: number | null;
  status: string;
  assigned_owner_id: string | null;
  hubspot_contact_id: string | null;
  hubspot_deal_id: string | null;
  appointment_status: string | null;
  last_error_code: string | null;
  created_at: string;
  updated_at: string;
};

export type WorkflowEvent = {
  id: string;
  lead_id: string;
  correlation_id: string | null;
  event_type: string;
  actor_type: string | null;
  actor_id: string | null;
  provider: string | null;
  result: string | null;
  details: Record<string, unknown> | null;
  error_code: string | null;
  error_message: string | null;
  created_at: string;
};

export type Communication = {
  id: string;
  lead_id: string;
  channel: string | null;
  template_key: string | null;
  provider: string | null;
  status: string | null;
  created_at: string;
  [key: string]: unknown;
};

export type Appointment = {
  id: string;
  lead_id: string;
  status: string | null;
  external_appointment_id: string | null;
  attendee_email: string | null;
  start_at: string | null;
  end_at: string | null;
  timezone: string | null;
  created_at: string;
  [key: string]: unknown;
};

export type LeadSort =
  | "newest"
  | "oldest"
  | "score_desc"
  | "score_asc"
  | "updated_desc";

export type LeadScoreBand =
  | "high"
  | "medium"
  | "low";

export type LeadFilters = {
  search?: string;
  status?: string;
  service?: string;
  source?: string;
  scoreBand?: string;
  owner?: string;
  createdFrom?: string;
  createdTo?: string;
  sort?: string;
  page?: number;
  pageSize?: number;
};

export type LeadListResult = {
  items: LeadListItem[];
  totalCount: number;
  page: number;
  pageSize: number;
  totalPages: number;
};

const leadListSelection = `
  id,
  correlation_id,
  source,
  full_name,
  email_normalized,
  phone_e164,
  service_type,
  location_text,
  service_zone,
  urgency,
  score,
  status,
  assigned_owner_id,
  hubspot_contact_id,
  hubspot_deal_id,
  appointment_status,
  last_error_code,
  created_at,
  updated_at
`;

function positiveInteger(
  value: number | undefined,
  fallback: number,
): number {
  return (
    typeof value === "number"
    && Number.isInteger(value)
    && value > 0
      ? value
      : fallback
  );
}

function safeSearchValue(
  value: string,
): string {
  return value
    .trim()
    .replace(
      /[^a-zA-Z0-9@+._\-\s]/g,
      " ",
    )
    .replace(/\s+/g, " ")
    .slice(0, 160);
}

function validDate(
  value: string | undefined,
): value is string {
  return (
    typeof value === "string"
    && /^\d{4}-\d{2}-\d{2}$/.test(
      value,
    )
  );
}

function validSort(
  value: string | undefined,
): LeadSort {
  switch (value) {
    case "oldest":
    case "score_desc":
    case "score_asc":
    case "updated_desc":
      return value;

    default:
      return "newest";
  }
}

export async function getLeads({
  search,
  status,
  service,
  source,
  scoreBand,
  owner,
  createdFrom,
  createdTo,
  sort,
  page,
  pageSize,
}: LeadFilters): Promise<LeadListResult> {
  const supabase = await createClient();

  const safePage =
    positiveInteger(page, 1);

  const safePageSize = Math.min(
    positiveInteger(pageSize, 25),
    100,
  );

  const from =
    (safePage - 1)
    * safePageSize;

  const to =
    from
    + safePageSize
    - 1;

  let query = supabase
    .from("leads")
    .select(
      leadListSelection,
      {
        count: "exact",
      },
    );

  if (status) {
    query = query.eq(
      "status",
      status,
    );
  }

  if (service) {
    query = query.eq(
      "service_type",
      service,
    );
  }

  if (source) {
    query = query.eq(
      "source",
      source,
    );
  }

  if (owner === "unassigned") {
    query = query.is(
      "assigned_owner_id",
      null,
    );
  } else if (owner) {
    query = query.eq(
      "assigned_owner_id",
      owner,
    );
  }

  switch (scoreBand) {
    case "high":
      query = query.gte(
        "score",
        80,
      );
      break;

    case "medium":
      query = query
        .gte("score", 55)
        .lt("score", 80);
      break;

    case "low":
      query = query.lt(
        "score",
        55,
      );
      break;
  }

  if (validDate(createdFrom)) {
    query = query.gte(
      "created_at",
      `${createdFrom}T00:00:00.000Z`,
    );
  }

  if (validDate(createdTo)) {
    query = query.lte(
      "created_at",
      `${createdTo}T23:59:59.999Z`,
    );
  }

  if (search) {
    const safeSearch =
      safeSearchValue(search);

    if (safeSearch) {
      query = query.or(
        [
          `correlation_id.ilike.%${safeSearch}%`,
          `full_name.ilike.%${safeSearch}%`,
          `email_normalized.ilike.%${safeSearch}%`,
          `phone_e164.ilike.%${safeSearch}%`,
          `location_text.ilike.%${safeSearch}%`,
          `service_type.ilike.%${safeSearch}%`,
          `source.ilike.%${safeSearch}%`,
          `assigned_owner_id.ilike.%${safeSearch}%`,
        ].join(","),
      );
    }
  }

  switch (validSort(sort)) {
    case "oldest":
      query = query.order(
        "created_at",
        {
          ascending: true,
        },
      );
      break;

    case "score_desc":
      query = query
        .order(
          "score",
          {
            ascending: false,
          },
        )
        .order(
          "created_at",
          {
            ascending: false,
          },
        );
      break;

    case "score_asc":
      query = query
        .order(
          "score",
          {
            ascending: true,
          },
        )
        .order(
          "created_at",
          {
            ascending: false,
          },
        );
      break;

    case "updated_desc":
      query = query.order(
        "updated_at",
        {
          ascending: false,
        },
      );
      break;

    default:
      query = query.order(
        "created_at",
        {
          ascending: false,
        },
      );
  }

  const {
    data,
    error,
    count,
  } = await query.range(
    from,
    to,
  );

  if (error) {
    throw new Error(
      `Unable to load leads: ${error.message}`,
    );
  }

  const totalCount = count ?? 0;
  const totalPages = Math.max(
    1,
    Math.ceil(
      totalCount / safePageSize,
    ),
  );

  if (
    totalCount > 0
    && safePage > totalPages
  ) {
    return getLeads({
      search,
      status,
      service,
      source,
      scoreBand,
      owner,
      createdFrom,
      createdTo,
      sort,
      page: totalPages,
      pageSize: safePageSize,
    });
  }

  return {
    items:
      (data ?? []) as LeadListItem[],

    totalCount,
    page: safePage,
    pageSize: safePageSize,
    totalPages,
  };
}

export async function getLeadOwners():
  Promise<string[]> {
  const supabase = await createClient();

  const {
    data,
    error,
  } = await supabase
    .from("leads")
    .select("assigned_owner_id")
    .not(
      "assigned_owner_id",
      "is",
      null,
    )
    .order(
      "assigned_owner_id",
      {
        ascending: true,
      },
    )
    .limit(1000);

  if (error) {
    throw new Error(
      `Unable to load lead owners: ${error.message}`,
    );
  }

  return Array.from(
    new Set(
      (data ?? [])
        .map(
          (
            row: {
              assigned_owner_id:
                string | null;
            },
          ) =>
            row.assigned_owner_id,
        )
        .filter(
          (
            value:
              string | null,
          ): value is string =>
            typeof value === "string"
            && value.length > 0,
        ),
    ),
  );
}

export async function getLead(
  leadId: string,
) {
  const supabase = await createClient();

  const {
    data,
    error,
  } = await supabase
    .from("leads")
    .select("*")
    .eq("id", leadId)
    .maybeSingle();

  if (error) {
    throw new Error(
      `Unable to load lead: ${error.message}`,
    );
  }

  return data as LeadListItem | null;
}

export async function getLeadWorkflowEvents(
  leadId: string,
) {
  const supabase = await createClient();

  const {
    data,
    error,
  } = await supabase
    .from("workflow_events")
    .select("*")
    .eq("lead_id", leadId)
    .order("created_at", {
      ascending: false,
    });

  if (error) {
    throw new Error(
      `Unable to load workflow events: ${error.message}`,
    );
  }

  return (data ?? []) as WorkflowEvent[];
}

export async function getLeadCommunications(
  leadId: string,
) {
  const supabase = await createClient();

  const {
    data,
    error,
  } = await supabase
    .from("communications")
    .select("*")
    .eq("lead_id", leadId)
    .order("created_at", {
      ascending: false,
    });

  if (error) {
    throw new Error(
      `Unable to load communications: ${error.message}`,
    );
  }

  return (data ?? []) as Communication[];
}

export async function getLeadAppointments(
  leadId: string,
) {
  const supabase = await createClient();

  const {
    data,
    error,
  } = await supabase
    .from("appointments")
    .select("*")
    .eq("lead_id", leadId)
    .order("created_at", {
      ascending: false,
    });

  if (error) {
    throw new Error(
      `Unable to load appointments: ${error.message}`,
    );
  }

  return (data ?? []) as Appointment[];
}

export type ReviewQueueLead =
  LeadListItem & {
    message: string | null;
    source: string | null;
  };


export async function getReviewQueue() {
  const supabase = await createClient();

  const {
    data,
    error,
  } = await supabase
    .from("leads")
    .select(
      `
        id,
        correlation_id,
        full_name,
        email_normalized,
        phone_e164,
        service_type,
        location_text,
        service_zone,
        urgency,
        score,
        status,
        assigned_owner_id,
        hubspot_contact_id,
        hubspot_deal_id,
        appointment_status,
        last_error_code,
        message,
        source,
        created_at,
        updated_at
      `,
    )
    .eq(
      "status",
      "REVIEW_REQUIRED",
    )
    .order("created_at", {
      ascending: true,
    });

  if (error) {
    throw new Error(
      `Unable to load review queue: ${error.message}`,
    );
  }

  return (data ?? []) as ReviewQueueLead[];
}


export async function getReviewReason(
  leadId: string,
) {
  const supabase = await createClient();

  const {
    data,
    error,
  } = await supabase
    .from("workflow_events")
    .select(
      `
        id,
        event_type,
        provider,
        result,
        details,
        error_code,
        error_message,
        created_at
      `,
    )
    .eq("lead_id", leadId)
    .order("created_at", {
      ascending: false,
    })
    .limit(20);

  if (error) {
    throw new Error(
      `Unable to load review reason: ${error.message}`,
    );
  }

  const events = (
    data ?? []
  ) as Array<
    Pick<
      WorkflowEvent,
      | "id"
      | "event_type"
      | "provider"
      | "result"
      | "details"
      | "error_code"
      | "error_message"
      | "created_at"
    >
  >;

  return (
    events.find(
      (event) =>
        event.event_type
          ?.toUpperCase()
          .includes("REVIEW") ||
        event.error_code ||
        event.result === "failed",
    ) ??
    events[0] ??
    null
  );
}