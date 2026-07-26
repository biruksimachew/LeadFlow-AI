import { redirect } from "next/navigation";

import { createClient } from "@/lib/supabase/server";

export async function requireOperator() {
  const supabase = await createClient();

  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user) {
    redirect("/login");
  }

  const {
    data: profile,
    error,
  } = await supabase
    .from("operator_profiles")
    .select(
      `
        user_id,
        display_name,
        role,
        is_active
      `,
    )
    .eq("user_id", user.id)
    .eq("is_active", true)
    .maybeSingle();

  if (error) {
    throw new Error(
      `Unable to load operator profile: ${error.message}`,
    );
  }

  return {
    supabase,
    user,
    profile,
  };
}