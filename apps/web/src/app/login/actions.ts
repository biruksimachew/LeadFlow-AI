"use server";

import { redirect } from "next/navigation";

import { createClient } from "@/lib/supabase/server";

export type LoginState = {
  error: string | null;
};

export async function login(
  _previousState: LoginState,
  formData: FormData,
): Promise<LoginState> {
  const email = formData.get("email");
  const password = formData.get("password");

  if (
    typeof email !== "string" ||
    typeof password !== "string" ||
    !email.trim() ||
    !password
  ) {
    return {
      error: "Email and password are required.",
    };
  }

  const supabase = await createClient();

  const { error } =
    await supabase.auth.signInWithPassword({
      email: email.trim(),
      password,
    });

  if (error) {
    console.error("Supabase login failed:", {
      message: error.message,
      status: error.status,
      code: error.code,
    });

    return {
      error: "Invalid email or password.",
    };
  }

  redirect("/dashboard");
}