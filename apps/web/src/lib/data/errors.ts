import {
  createClient,
} from "@/lib/supabase/server";


export type WorkflowErrorItem = {
  id: string;
  lead_id: string;
  correlation_id: string;

  failed_action: string;

  provider: string | null;

  error_code: string;
  error_message: string | null;

  retryable: boolean;
  retry_count: number;

  status:
    | "OPEN"
    | "RETRYING"
    | "RESOLVED"
    | "DEAD_LETTER";

  next_retry_at: string | null;

  created_at: string;
  updated_at: string;

  lead: {
    full_name: string | null;
    email_normalized: string | null;
    service_type: string | null;
    status: string;
  } | null;
};


export async function getWorkflowErrors():
  Promise<WorkflowErrorItem[]> {

  const supabase =
    await createClient();

  const {
    data: errors,
    error,
  } =
    await supabase
      .from("workflow_errors")
      .select("*")
      .in(
        "status",
        [
          "OPEN",
          "RETRYING",
          "DEAD_LETTER",
        ],
      )
      .order(
        "created_at",
        {
          ascending: false,
        },
      );

  if (error) {
    throw new Error(
      `Unable to load workflow errors: ${error.message}`,
    );
  }

  if (
    !errors ||
    errors.length === 0
  ) {
    return [];
  }

  const leadIds = [
    ...new Set(
      errors.map(
        (item) =>
          item.lead_id,
      ),
    ),
  ];

  const {
    data: leads,
    error: leadsError,
  } =
    await supabase
      .from("leads")
      .select(
        `
        id,
        full_name,
        email_normalized,
        service_type,
        status
        `,
      )
      .in(
        "id",
        leadIds,
      );

  if (leadsError) {
    throw new Error(
      `Unable to load error leads: ${leadsError.message}`,
    );
  }

  const leadMap =
    new Map(
      (leads ?? []).map(
        (lead) => [
          lead.id,
          lead,
        ],
      ),
    );

  return errors.map(
    (item) => ({
      ...item,

      lead:
        leadMap.get(
          item.lead_id,
        ) ?? null,
    }),
  ) as WorkflowErrorItem[];
}


export async function
getCurrentOperatorRole():
  Promise<string | null> {

  const supabase =
    await createClient();

  const {
    data: {
      user,
    },
  } =
    await supabase.auth.getUser();

  if (!user) {
    return null;
  }

  const {
    data,
  } =
    await supabase
      .from(
        "operator_profiles",
      )
      .select("role")
      .eq(
        "user_id",
        user.id,
      )
      .maybeSingle();

  return data?.role ?? null;
}