"use server";

import { randomUUID } from "node:crypto";
import { createClient } from "@/lib/supabase/server";
import { submitLeadToN8n } from "@/lib/leadflow/n8n";

export type MetaSimulatorState = {
  success: boolean;
  error: string | null;
  status: string | null;
  outcome: string | null;
  eventId: string | null;
};

const emptyState: MetaSimulatorState = {
  success: false,
  error: null,
  status: null,
  outcome: null,
  eventId: null,
};

function value(formData: FormData, key: string): string {
  const item = formData.get(key);
  return typeof item === "string" ? item.trim() : "";
}

export async function simulateMetaLead(
  _previousState: MetaSimulatorState,
  formData: FormData,
): Promise<MetaSimulatorState> {
  try {
    const supabase = await createClient();
    const {
      data: { user },
    } = await supabase.auth.getUser();

    if (!user) {
      return { ...emptyState, error: "Operator session required." };
    }

    const fullName = value(formData, "full_name");
    const email = value(formData, "email");
    const phone = value(formData, "phone");
    const serviceType = value(formData, "service_type");
    const location = value(formData, "location");
    const urgency = value(formData, "urgency");
    const message = value(formData, "message");
    const campaignName = value(formData, "campaign_name");

    if (!fullName || !email || !serviceType || !location || !urgency) {
      return { ...emptyState, error: "Complete all required fields." };
    }

    const eventId = `meta_${randomUUID()}`;

    const result = await submitLeadToN8n(
      {
        full_name: fullName,
        email,
        phone: phone || null,
        service_type: serviceType,
        location,
        urgency,
        message: campaignName
          ? `${message}\n\nMeta campaign: ${campaignName}`
          : message || null,
        source: "meta",
        preferred_contact: "email",
        consent_marketing: formData.get("consent_marketing") === "on",
      },
      eventId,
    );

    return {
      success: true,
      error: null,
      status: typeof result.status === "string" ? result.status : null,
      outcome:
        typeof result.workflow_outcome === "string"
          ? result.workflow_outcome
          : null,
      eventId,
    };
  } catch (error) {
    return {
      ...emptyState,
      error: error instanceof Error ? error.message : "Meta simulation failed.",
    };
  }
}
