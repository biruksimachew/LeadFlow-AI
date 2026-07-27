export type LeadFlowWebhookResponse = {
  success?: boolean;
  stage?: string;
  lead_id?: string;
  status?: string;
  workflow_outcome?: string;
  [key: string]: unknown;
};

function webhookUrl(): string {
  const value = process.env.N8N_LEAD_WEBHOOK_URL;
  if (!value) {
    throw new Error("N8N_LEAD_WEBHOOK_URL is not configured.");
  }
  return value;
}

export async function submitLeadToN8n(
  payload: Record<string, unknown>,
  idempotencyKey: string,
): Promise<LeadFlowWebhookResponse> {
  const response = await fetch(webhookUrl(), {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "Idempotency-Key": idempotencyKey,
    },
    body: JSON.stringify(payload),
    cache: "no-store",
  });

  const body = await response.json().catch(() => null);

  if (!response.ok) {
    const message =
      typeof body?.detail === "string"
        ? body.detail
        : typeof body?.detail?.message === "string"
          ? body.detail.message
          : "LeadFlow orchestration request failed.";
    throw new Error(message);
  }

  return (body ?? {}) as LeadFlowWebhookResponse;
}
