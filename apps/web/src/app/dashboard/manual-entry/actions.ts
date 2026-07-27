"use server";

import {
  randomUUID,
} from "node:crypto";

import {
  revalidatePath,
} from "next/cache";

import {
  createClient,
} from "@/lib/supabase/server";


type IntakeResponse = {
  success: boolean;

  intake_id: string;
  correlation_id: string;

  status: string;

  replayed: boolean;
  duplicate: boolean;

  message: string;
};


export type ManualEntryState = {
  success: boolean;
  error: string | null;

  status: string | null;
  intakeId: string | null;
  correlationId: string | null;

  duplicate: boolean;
  replayed: boolean;
};


export type CsvRowResult = {
  row: number;
  name: string;

  success: boolean;
  status: string | null;

  duplicate: boolean;
  replayed: boolean;

  message: string;
};


export type CsvImportState = {
  success: boolean;
  error: string | null;

  total: number;
  succeeded: number;
  failed: number;
  duplicates: number;

  results: CsvRowResult[];
};


const initialManualState:
  ManualEntryState = {
    success: false,
    error: null,

    status: null,
    intakeId: null,
    correlationId: null,

    duplicate: false,
    replayed: false,
  };


function getApiUrl(): string {
  const apiUrl =
    process.env.NEXT_PUBLIC_API_URL;

  if (!apiUrl) {
    throw new Error(
      "NEXT_PUBLIC_API_URL is not configured.",
    );
  }

  return apiUrl.replace(
    /\/$/,
    "",
  );
}


async function getOperatorToken():
  Promise<string> {

  const supabase =
    await createClient();

  const {
    data: {
      user,
    },
    error: userError,
  } =
    await supabase.auth.getUser();

  if (
    userError ||
    !user
  ) {
    throw new Error(
      "Your operator session has expired.",
    );
  }

  const {
    data: profile,
    error: profileError,
  } =
    await supabase
      .from(
        "operator_profiles",
      )
      .select(
        "role",
      )
      .eq(
        "user_id",
        user.id,
      )
      .maybeSingle();

  if (
    profileError ||
    !profile
  ) {
    throw new Error(
      "Operator access is required.",
    );
  }

  const {
    data: {
      session,
    },
  } =
    await supabase.auth.getSession();

  if (
    !session?.access_token
  ) {
    throw new Error(
      "Unable to obtain operator session.",
    );
  }

  return session.access_token;
}


function readString(
  formData: FormData,
  key: string,
): string {

  const value =
    formData.get(key);

  return (
    typeof value === "string"
      ? value.trim()
      : ""
  );
}


function nullable(
  value: string,
): string | null {

  return value.length
    ? value
    : null;
}


function formatApiError(
  body: unknown,
): string {

  if (
    typeof body !== "object" ||
    body === null
  ) {
    return "Lead intake failed.";
  }

  const object =
    body as Record<
      string,
      unknown
    >;

  const detail =
    object.detail;

  if (
    typeof detail === "string"
  ) {
    return detail;
  }

  if (
    Array.isArray(detail)
  ) {
    return detail
      .map((item) => {

        if (
          typeof item !== "object" ||
          item === null
        ) {
          return String(item);
        }

        const row =
          item as Record<
            string,
            unknown
          >;

        const location =
          Array.isArray(
            row.loc,
          )
            ? row.loc.join(".")
            : "";

        const message =
          typeof row.msg
            === "string"
            ? row.msg
            : "Invalid value";

        return location
          ? `${location}: ${message}`
          : message;
      })
      .join("; ");
  }

  if (
    typeof detail === "object" &&
    detail !== null
  ) {
    const row =
      detail as Record<
        string,
        unknown
      >;

    if (
      typeof row.message
      === "string"
    ) {
      return row.message;
    }

    if (
      typeof row.code
      === "string"
    ) {
      return row.code;
    }
  }

  return "Lead intake failed.";
}


async function submitIntake(
  payload: Record<string, unknown>,
  options: {
    idempotencyKey: string;
    token: string;
  },
): Promise<IntakeResponse> {

  const {
    idempotencyKey,
    token,
  } = options;

  const response =
    await fetch(
      `${getApiUrl()}/api/v1/leads/intake`,
      {
        method: "POST",

        headers: {
          "Content-Type":
            "application/json",

          "Idempotency-Key":
            idempotencyKey,

          Authorization:
            `Bearer ${token}`,
        },

        body:
          JSON.stringify(
            payload,
          ),

        cache: "no-store",
      },
    );

  const body =
    await response
      .json()
      .catch(
        () => null,
      );

  if (!response.ok) {
    throw new Error(
      formatApiError(body),
    );
  }

  return body as IntakeResponse;
}

function revalidateOperations() {
  revalidatePath(
    "/dashboard",
  );

  revalidatePath(
    "/dashboard/leads",
  );

  revalidatePath(
    "/dashboard/review",
  );

  revalidatePath(
    "/dashboard/errors",
  );

  revalidatePath(
    "/dashboard/manual-entry",
  );
}


export async function submitManualLead(
  _previousState: ManualEntryState,
  formData: FormData,
): Promise<ManualEntryState> {

  try {

    const fullName =
      readString(
        formData,
        "full_name",
      );

    const email =
      readString(
        formData,
        "email",
      );

    const phone =
      readString(
        formData,
        "phone",
      );

    const serviceType =
      readString(
        formData,
        "service_type",
      );

    const location =
      readString(
        formData,
        "location",
      );

    const urgency =
      readString(
        formData,
        "urgency",
      );

    const message =
      readString(
        formData,
        "message",
      );

    const preferredContact =
      readString(
        formData,
        "preferred_contact",
      ) || "unknown";

    if (
      !fullName ||
      !serviceType ||
      !location ||
      !urgency
    ) {
      return {
        ...initialManualState,

        error:
          "Complete all required fields.",
      };
    }

    if (
      !email &&
      !phone
    ) {
      return {
        ...initialManualState,

        error:
          "Enter at least an email address or phone number.",
      };
    }

    const token =
      await getOperatorToken();

    const result =
      await submitIntake(
        {
          full_name:
            fullName,

          email:
            nullable(email),

          phone:
            nullable(phone),

          service_type:
            serviceType,

          location,

          urgency,

          message:
            nullable(message),

          source:
            "manual",

          preferred_contact:
            preferredContact,

          consent_marketing:
            formData.get(
              "consent_marketing",
            ) === "on",
        },
        {
          idempotencyKey:
            `manual-${randomUUID()}`,

          token,
        },
      );

    revalidateOperations();

    return {
      success: true,
      error: null,

      status:
        result.status,

      intakeId:
        result.intake_id,

      correlationId:
        result.correlation_id,

      duplicate:
        result.duplicate,

      replayed:
        result.replayed,
    };

  } catch (error) {

    return {
      ...initialManualState,

      error:
        error instanceof Error
          ? error.message
          : (
            "Unable to submit lead."
          ),
    };
  }
}


// ==========================================================
// CSV
// ==========================================================

function parseCsv(
  text: string,
): string[][] {

  const rows:
    string[][] = [];

  let row:
    string[] = [];

  let field = "";

  let quoted = false;

  for (
    let index = 0;
    index < text.length;
    index += 1
  ) {
    const char =
      text[index];

    const next =
      text[index + 1];

    if (
      char === "\""
    ) {
      if (
        quoted &&
        next === "\""
      ) {
        field += "\"";
        index += 1;
      } else {
        quoted = !quoted;
      }

      continue;
    }

    if (
      char === "," &&
      !quoted
    ) {
      row.push(field);
      field = "";

      continue;
    }

    if (
      (
        char === "\n" ||
        char === "\r"
      ) &&
      !quoted
    ) {
      if (
        char === "\r" &&
        next === "\n"
      ) {
        index += 1;
      }

      row.push(field);

      if (
        row.some(
          (value) =>
            value.trim()
              .length > 0,
        )
      ) {
        rows.push(row);
      }

      row = [];
      field = "";

      continue;
    }

    field += char;
  }

  row.push(field);

  if (
    row.some(
      (value) =>
        value.trim()
          .length > 0,
    )
  ) {
    rows.push(row);
  }

  return rows;
}


function parseConsent(
  value: string,
): boolean {

  return [
    "true",
    "1",
    "yes",
    "y",
  ].includes(
    value
      .trim()
      .toLowerCase(),
  );
}


export async function importLeadCsv(
  _previousState: CsvImportState,
  formData: FormData,
): Promise<CsvImportState> {

  const empty:
    CsvImportState = {
      success: false,
      error: null,

      total: 0,
      succeeded: 0,
      failed: 0,
      duplicates: 0,

      results: [],
    };

  try {

    const upload =
      formData.get(
        "file",
      );

    if (
      !(upload instanceof File)
    ) {
      return {
        ...empty,

        error:
          "Choose a CSV file.",
      };
    }

    if (
      upload.size === 0
    ) {
      return {
        ...empty,

        error:
          "The CSV file is empty.",
      };
    }

    const text =
      await upload.text();

    const rows =
      parseCsv(text);

    if (
      rows.length < 2
    ) {
      return {
        ...empty,

        error:
          "CSV must contain a header and at least one lead.",
      };
    }

    const headers =
      rows[0].map(
        (header) =>
          header
            .trim()
            .toLowerCase(),
      );

    const required =
      [
        "full_name",
        "service_type",
        "location",
        "urgency",
      ];

    const missing =
      required.filter(
        (header) =>
          !headers.includes(
            header,
          ),
      );

    if (
      missing.length
    ) {
      return {
        ...empty,

        error:
          `Missing required CSV columns: ${missing.join(", ")}`,
      };
    }

    if (
      !headers.includes(
        "email",
      ) &&
      !headers.includes(
        "phone",
      )
    ) {
      return {
        ...empty,

        error:
          "CSV must contain an email or phone column.",
      };
    }

    const dataRows =
      rows.slice(1);

    if (
      dataRows.length > 100
    ) {
      return {
        ...empty,

        error:
          "CSV test imports are limited to 100 rows.",
      };
    }

    const token =
      await getOperatorToken();

    const results:
      CsvRowResult[] = [];

    for (
      let index = 0;
      index < dataRows.length;
      index += 1
    ) {
      const values =
        dataRows[index];

      const record:
        Record<
          string,
          string
        > = {};

      headers.forEach(
        (
          header,
          column,
        ) => {
          record[header] =
            (
              values[
                column
              ] ?? ""
            ).trim();
        },
      );

      const displayName =
        record.full_name ||
        `Row ${index + 2}`;

      try {

        if (
          !record.email &&
          !record.phone
        ) {
          throw new Error(
            "At least one contact method is required.",
          );
        }

        const result =
          await submitIntake(
            {
              full_name:
                record.full_name,

              email:
                nullable(
                  record.email ??
                  "",
                ),

              phone:
                nullable(
                  record.phone ??
                  "",
                ),

              service_type:
                record.service_type,

              location:
                record.location,

              urgency:
                record.urgency,

              message:
                nullable(
                  record.message ??
                  "",
                ),

              source:
                "csv_test",

              preferred_contact:
                record
                  .preferred_contact ||
                "unknown",

              consent_marketing:
                parseConsent(
                  record
                    .consent_marketing ??
                  "",
                ),
            },
            {
              idempotencyKey:
                `csv-${randomUUID()}-${index + 1}`,

              token,
            },
          );

        results.push({
          row:
            index + 2,

          name:
            displayName,

          success: true,

          status:
            result.status,

          duplicate:
            result.duplicate,

          replayed:
            result.replayed,

          message:
            result.message,
        });

      } catch (error) {

        results.push({
          row:
            index + 2,

          name:
            displayName,

          success: false,
          status: null,

          duplicate: false,
          replayed: false,

          message:
            error instanceof Error
              ? error.message
              : (
                "Lead import failed."
              ),
        });
      }
    }

    revalidateOperations();

    const succeeded =
      results.filter(
        (row) =>
          row.success,
      ).length;

    const failed =
      results.length -
      succeeded;

    const duplicates =
      results.filter(
        (row) =>
          row.duplicate,
      ).length;

    return {
      success:
        failed === 0,

      error: null,

      total:
        results.length,

      succeeded,
      failed,
      duplicates,

      results,
    };

  } catch (error) {

    return {
      ...empty,

      error:
        error instanceof Error
          ? error.message
          : (
            "Unable to import CSV."
          ),
    };
  }
}