"use server";

import {
  revalidatePath,
} from "next/cache";

import { createClient } from "@/lib/supabase/server";


export type ReviewActionState = {
  error: string | null;
  success: boolean;
};


export async function resolveReview(
  _previousState: ReviewActionState,
  formData: FormData,
): Promise<ReviewActionState> {
  const leadId =
    formData.get("lead_id");

  const status =
    formData.get("status");

  const reason =
    formData.get("reason");

  if (
    typeof leadId !== "string" ||
    typeof status !== "string" ||
    typeof reason !== "string"
  ) {
    return {
      success: false,
      error: "Invalid review request.",
    };
  }

  if (
    reason.trim().length < 10
  ) {
    return {
      success: false,
      error:
        "Please enter a meaningful reason.",
    };
  }

  const supabase =
    await createClient();

  const {
    data: { user },
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

  const accessToken =
    session?.access_token;

  if (!accessToken) {
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
      `${apiUrl}/api/v1/leads/${leadId}/override`,
      {
        method: "POST",

        headers: {
          "Content-Type":
            "application/json",

          Authorization:
            `Bearer ${accessToken}`,
        },

        body: JSON.stringify({
          status,
          reason:
            reason.trim(),
        }),

        cache: "no-store",
      },
    );

  if (!response.ok) {
    const body =
      await response
        .json()
        .catch(
          () => null,
        );

    const message =
      body?.detail?.message ??
      body?.detail?.code ??
      "Unable to resolve review.";

    return {
      success: false,
      error: message,
    };
  }

  revalidatePath(
    "/dashboard"
  );

  revalidatePath(
    "/dashboard/review"
  );

  revalidatePath(
    "/dashboard/leads"
  );

  revalidatePath(
    `/dashboard/leads/${leadId}`
  );

  return {
    success: true,
    error: null,
  };
}