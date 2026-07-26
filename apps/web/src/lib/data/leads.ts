import { createClient } from "@/lib/supabase/server";

export type LeadListItem = {
  id: string;
  correlation_id: string | null;
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

type LeadFilters = {
  search?: string;
  status?: string;
  service?: string;
};

export async function getLeads({
  search,
  status,
  service,
}: LeadFilters) {
  const supabase = await createClient();

  let query = supabase
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
        created_at,
        updated_at
      `,
    )
    .order("created_at", {
      ascending: false,
    })
    .limit(100);

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

  if (search) {
    const safeSearch = search
      .trim()
      .replace(/[,%()]/g, " ");

    if (safeSearch) {
      query = query.or(
        [
          `full_name.ilike.%${safeSearch}%`,
          `email_normalized.ilike.%${safeSearch}%`,
          `phone_e164.ilike.%${safeSearch}%`,
          `location_text.ilike.%${safeSearch}%`,
          `service_type.ilike.%${safeSearch}%`,
        ].join(","),
      );
    }
  }

  const {
    data,
    error,
  } = await query;

  if (error) {
    throw new Error(
      `Unable to load leads: ${error.message}`,
    );
  }

  return (data ?? []) as LeadListItem[];
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