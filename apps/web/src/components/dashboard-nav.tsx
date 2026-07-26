"use client";

import {
  AlertTriangle,
  ClipboardPlus,
  LayoutDashboard,
  ListChecks,
  Users,
} from "lucide-react";

import Link from "next/link";
import { usePathname } from "next/navigation";

const navigation = [
  {
    name: "Dashboard",
    href: "/dashboard",
    icon: LayoutDashboard,
  },
  {
    name: "Leads",
    href: "/dashboard/leads",
    icon: Users,
  },
  {
    name: "Review Queue",
    href: "/dashboard/review",
    icon: ListChecks,
  },
  {
    name: "Workflow Errors",
    href: "/dashboard/errors",
    icon: AlertTriangle,
  },
  {
    name: "Manual Entry",
    href: "/dashboard/manual-entry",
    icon: ClipboardPlus,
  },
];

export function DashboardNav() {
  const pathname = usePathname();

  return (
    <nav className="space-y-1">
      {navigation.map((item) => {
        const Icon = item.icon;

        const active =
          item.href === "/dashboard"
            ? pathname === item.href
            : pathname.startsWith(
                item.href,
              );

        return (
          <Link
            key={item.href}
            href={item.href}
            className={[
              "flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition",
              active
                ? "bg-slate-900 text-white"
                : "text-slate-600 hover:bg-slate-100 hover:text-slate-950",
            ].join(" ")}
          >
            <Icon
              className="h-4 w-4"
            />

            {item.name}
          </Link>
        );
      })}
    </nav>
  );
}