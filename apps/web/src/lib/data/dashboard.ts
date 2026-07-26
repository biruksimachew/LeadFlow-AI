import { createClient } from "@/lib/supabase/server";

type DashboardStats = {
  totalLeads: number;
  hotLeads: number;
  reviewRequired: number;
  appointmentsBooked: number;
};

export async function getDashboardStats(): Promise<DashboardStats> {
  const supabase = await createClient();

  const [
    totalResult,
    hotResult,
    reviewResult,
    bookedResult,
  ] = await Promise.all([
    supabase
      .from("leads")
      .select("*", {
        count: "exact",
        head: true,
      }),

    supabase
      .from("leads")
      .select("*", {
        count: "exact",
        head: true,
      })
      .eq("status", "QUALIFIED_HOT"),

    supabase
      .from("leads")
      .select("*", {
        count: "exact",
        head: true,
      })
      .eq("status", "REVIEW_REQUIRED"),

    supabase
      .from("leads")
      .select("*", {
        count: "exact",
        head: true,
      })
      .eq(
        "status",
        "APPOINTMENT_BOOKED",
      ),
  ]);

  const results = [
    totalResult,
    hotResult,
    reviewResult,
    bookedResult,
  ];

  const failedResult =
    results.find(
      (result) => result.error,
    );

  if (failedResult?.error) {
    throw new Error(
      `Unable to load dashboard statistics: ${failedResult.error.message}`,
    );
  }

  return {
    totalLeads:
      totalResult.count ?? 0,

    hotLeads:
      hotResult.count ?? 0,

    reviewRequired:
      reviewResult.count ?? 0,

    appointmentsBooked:
      bookedResult.count ?? 0,
  };
}