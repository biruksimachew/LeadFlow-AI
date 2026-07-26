import type { ReactNode } from "react";

import { DashboardNav } from "@/components/dashboard-nav";
import { requireOperator } from "@/lib/auth/require-operator";

import { logout } from "./actions";

type DashboardLayoutProps = {
  children: ReactNode;
};

export default async function DashboardLayout({
  children,
}: DashboardLayoutProps) {
  const {
    user,
    profile,
  } = await requireOperator();

  if (!profile) {
    return (
      <main className="flex min-h-screen items-center justify-center bg-slate-100 px-6">
        <div className="w-full max-w-lg rounded-2xl border border-slate-200 bg-white p-8">
          <p className="text-sm font-semibold text-red-600">
            Access denied
          </p>

          <h1 className="mt-2 text-2xl font-semibold text-slate-950">
            Operator access required
          </h1>

          <p className="mt-3 text-sm leading-6 text-slate-600">
            Your account is authenticated,
            but it does not have an active
            LeadFlow operator profile.
          </p>

          <form
            action={logout}
            className="mt-6"
          >
            <button
              type="submit"
              className="rounded-lg bg-slate-950 px-4 py-2 text-sm font-medium text-white"
            >
              Sign out
            </button>
          </form>
        </div>
      </main>
    );
  }

  return (
    <div className="min-h-screen bg-slate-100">
      <aside className="fixed inset-y-0 left-0 hidden w-64 border-r border-slate-200 bg-white lg:block">
        <div className="flex h-20 items-center border-b border-slate-200 px-6">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">
              NorthStar
            </p>

            <p className="mt-1 text-lg font-semibold text-slate-950">
              LeadFlow AI
            </p>
          </div>
        </div>

        <div className="p-4">
          <DashboardNav />
        </div>

        <div className="absolute bottom-0 left-0 right-0 border-t border-slate-200 p-4">
          <p className="truncate text-sm font-medium text-slate-950">
            {profile.display_name ??
              "Operator"}
          </p>

          <p className="mt-1 truncate text-xs text-slate-500">
            {user.email}
          </p>

          <p className="mt-1 text-xs font-semibold text-slate-500">
            {profile.role}
          </p>

          <form
            action={logout}
            className="mt-4"
          >
            <button
              type="submit"
              className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm font-medium text-slate-700 transition hover:bg-slate-50"
            >
              Sign out
            </button>
          </form>
        </div>
      </aside>

      <main className="lg:pl-64">
        <div className="mx-auto max-w-7xl px-6 py-8">
          {children}
        </div>
      </main>
    </div>
  );
}