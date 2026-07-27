"use server";

import {
  revalidatePath,
} from "next/cache";

import {
  createClient,
} from "@/lib/supabase/server";


export type RetryState = {
  success: boolean;
  error: string | null;
};


export async function retryWorkflow(
  _previousState: RetryState,
  formData: FormData,
): Promise<RetryState> {

  const errorId =
    formData.get(
      "error_id",
    );

  const reason =
    formData.get(
      "reason",
    );

  if (
    typeof errorId
      !== "string" ||
    typeof reason
      !== "string"
  ) {
    return {
      success: false,
      error:
        "Invalid retry request.",
    };
  }

  if (
    reason.trim().length
      < 10
  ) {
    return {
      success: false,
      error:
        "Enter a meaningful retry reason.",
    };
  }

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
    return {
      success: false,
      error:
        "Your session has expired.",
    };
  }

  const {
    data: {
      session,
    },
  } =
    await supabase.auth.getSession();

  const token =
    session?.access_token;

  if (!token) {
    return {
      success: false,
      error:
        "Unable to obtain operator session.",
    };
  }

  const apiUrl =
    process.env
      .NEXT_PUBLIC_API_URL;

  const response =
    await fetch(
      `${apiUrl}/api/v1/workflow-errors/${errorId}/retry`,
      {
        method: "POST",

        headers: {
          "Content-Type":
            "application/json",

          Authorization:
            `Bearer ${token}`,
        },

        body: JSON.stringify({
          reason:
            reason.trim(),
        }),

        cache: "no-store",
      },
    );

  const body =
    await response
      .json()
      .catch(
        () => null,
      );

  revalidatePath(
    "/dashboard/errors",
  );

  revalidatePath(
    "/dashboard/leads",
  );

  if (!response.ok) {
    return {
      success: false,

      error:
        body?.detail
          ?.message ??
        body?.detail
          ?.code ??
        "Unable to retry workflow.",
    };
  }

  if (
    body?.retry_status
      !== "SUCCEEDED"
  ) {
    return {
      success: false,

      error:
        `Retry completed but the workflow is still failing${
          body?.error_code
            ? `: ${body.error_code}`
            : "."
        }`,
    };
  }

  return {
    success: true,
    error: null,
  };
}