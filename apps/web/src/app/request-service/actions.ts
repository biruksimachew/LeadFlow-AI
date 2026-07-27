"use server";

import { randomUUID } from "node:crypto";
import { submitLeadToN8n } from "@/lib/leadflow/n8n";

export type ServiceRequestState = {
  success: boolean;
  error: string | null;
  leadId: string | null;
};

const emptyState: ServiceRequestState = {
  success: false,
  error: null,
  leadId: null,
};

function value(formData: FormData, key: string): string {
  const item = formData.get(key);
  return typeof item === "string" ? item.trim() : "";
}

export async function submitServiceRequest(
  _previousState: ServiceRequestState,
  formData: FormData,
): Promise<ServiceRequestState> {
  try {
    const fullName = value(formData, "full_name");
    const email = value(formData, "email");
    const phone = value(formData, "phone");
    const serviceType = value(formData, "service_type");
    const location = value(formData, "location");
    const urgency = value(formData, "urgency");
    const message = value(formData, "message");
    const preferredContact = value(formData, "preferred_contact") || "unknown";

    if (!fullName || !serviceType || !location || !urgency) {
      return { ...emptyState, error: "Complete all required fields." };
    }

    if (!email && !phone) {
      return { ...emptyState, error: "Provide an email address or phone number." };
    }

    const result = await submitLeadToN8n(
      {
        full_name: fullName,
        email: email || null,
        phone: phone || null,
        service_type: serviceType,
        location,
        urgency,
        message: message || null,
        source: "website",
        preferred_contact: preferredContact,
        consent_marketing: formData.get("consent_marketing") === "on",
      },
      `website-${randomUUID()}`,
    );

    return {
      success: true,
      error: null,
      leadId: typeof result.lead_id === "string" ? result.lead_id : null,
    };
  } catch (error) {
    return {
      ...emptyState,
      error: error instanceof Error ? error.message : "Request submission failed.",
    };
  }
}
