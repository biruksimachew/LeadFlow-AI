import "server-only";

export type LeadFlowIntakeReceipt = {
  success: true;
  stage: "INTAKE";

  lead_id: string;
  intake_id: string;
  correlation_id: string;

  status: string;
  duplicate: boolean;
  replayed: boolean;
  continue_processing: boolean;

  [key: string]: unknown;
};

function webhookUrl(): string {
  const value =
    process.env.N8N_LEAD_WEBHOOK_URL?.trim();

  if (!value) {
    throw new Error(
      "N8N_LEAD_WEBHOOK_URL is not configured.",
    );
  }

  return value;
}

function ingressToken(): string {
  const value =
    process.env.LEADFLOW_INGRESS_TOKEN?.trim();

  if (!value) {
    throw new Error(
      "LEADFLOW_INGRESS_TOKEN is not configured.",
    );
  }

  return value;
}

function errorMessage(body: unknown): string {
  if (!body || typeof body !== "object") {
    return "LeadFlow intake request failed.";
  }

  if (
    "detail" in body
    && typeof body.detail === "string"
  ) {
    return body.detail;
  }

  if (
    "detail" in body
    && body.detail
    && typeof body.detail === "object"
    && "message" in body.detail
    && typeof body.detail.message === "string"
  ) {
    return body.detail.message;
  }

  if (
    "message" in body
    && typeof body.message === "string"
  ) {
    return body.message;
  }

  return "LeadFlow intake request failed.";
}

function isIntakeReceipt(
  body: unknown,
): body is LeadFlowIntakeReceipt {
  if (!body || typeof body !== "object") {
    return false;
  }

  const candidate =
    body as Partial<LeadFlowIntakeReceipt>;

  return (
    candidate.success === true
    && candidate.stage === "INTAKE"
    && typeof candidate.lead_id === "string"
    && typeof candidate.intake_id === "string"
    && typeof candidate.correlation_id === "string"
    && typeof candidate.status === "string"
    && typeof candidate.duplicate === "boolean"
    && typeof candidate.replayed === "boolean"
    && typeof candidate.continue_processing
      === "boolean"
  );
}

export async function submitLeadToN8n(
  payload: Record<string, unknown>,
  idempotencyKey: string,
): Promise<LeadFlowIntakeReceipt> {
  const response = await fetch(webhookUrl(), {
    method: "POST",

    headers: {
      "Content-Type": "application/json",
      "Idempotency-Key": idempotencyKey,
      "X-LeadFlow-Ingress-Token":
        ingressToken(),
    },

    body: JSON.stringify(payload),
    cache: "no-store",
    signal: AbortSignal.timeout(5_000),
  });

  const body: unknown = await response
    .json()
    .catch(() => null);

  if (response.status !== 202) {
    throw new Error(errorMessage(body));
  }

  if (!isIntakeReceipt(body)) {
    throw new Error(
      "LeadFlow returned an invalid intake receipt.",
    );
  }

  return body;
}
