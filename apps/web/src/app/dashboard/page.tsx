import {
  CalendarCheck,
  Flame,
  ListChecks,
  Users,
} from "lucide-react";

import { getDashboardStats } from "@/lib/data/dashboard";

export default async function DashboardPage() {
  const stats =
    await getDashboardStats();

  const cards = [
    {
      label: "Total Leads",
      value: stats.totalLeads,
      icon: Users,
    },
    {
      label: "Hot Leads",
      value: stats.hotLeads,
      icon: Flame,
    },
    {
      label: "Review Queue",
      value: stats.reviewRequired,
      icon: ListChecks,
    },
    {
      label: "Appointments Booked",
      value:
        stats.appointmentsBooked,
      icon: CalendarCheck,
    },
  ];

  return (
    <>
      <div>
        <p className="text-sm font-medium text-slate-500">
          Operations overview
        </p>

        <h1 className="mt-1 text-3xl font-semibold tracking-tight text-slate-950">
          Dashboard
        </h1>

        <p className="mt-2 text-sm text-slate-600">
          Live operational state from
          LeadFlow AI.
        </p>
      </div>

      <div className="mt-8 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {cards.map(
          ({
            label,
            value,
            icon: Icon,
          }) => (
            <div
              key={label}
              className="rounded-xl border border-slate-200 bg-white p-5"
            >
              <div className="flex items-center justify-between">
                <p className="text-sm font-medium text-slate-500">
                  {label}
                </p>

                <Icon className="h-5 w-5 text-slate-400" />
              </div>

              <p className="mt-4 text-3xl font-semibold tracking-tight text-slate-950">
                {value}
              </p>
            </div>
          ),
        )}
      </div>

      <div className="mt-8 rounded-xl border border-slate-200 bg-white p-6">
        <h2 className="text-lg font-semibold text-slate-950">
          System status
        </h2>

        <div className="mt-5 grid gap-4 sm:grid-cols-3">
          <Status
            label="Lead intake"
            value="Operational"
          />

          <Status
            label="CRM synchronization"
            value="Operational"
          />

          <Status
            label="Communication engine"
            value="Operational"
          />
        </div>
      </div>
    </>
  );
}

function Status({
  label,
  value,
}: {
  label: string;
  value: string;
}) {
  return (
    <div className="rounded-lg bg-slate-50 p-4">
      <p className="text-sm text-slate-500">
        {label}
      </p>

      <div className="mt-2 flex items-center gap-2">
        <span className="h-2 w-2 rounded-full bg-emerald-500" />

        <span className="text-sm font-medium text-slate-900">
          {value}
        </span>
      </div>
    </div>
  );
}