type LeadStatusBadgeProps = {
  status: string;
};

const statusStyles: Record<
  string,
  string
> = {
  QUALIFIED_HOT:
    "bg-red-50 text-red-700 ring-red-600/20",

  QUALIFIED_WARM:
    "bg-amber-50 text-amber-700 ring-amber-600/20",

  COLD:
    "bg-sky-50 text-sky-700 ring-sky-600/20",

  REVIEW_REQUIRED:
    "bg-purple-50 text-purple-700 ring-purple-600/20",

  DISQUALIFIED:
    "bg-slate-100 text-slate-600 ring-slate-500/20",

  APPOINTMENT_BOOKED:
    "bg-emerald-50 text-emerald-700 ring-emerald-600/20",

  BOOKING_SENT:
    "bg-blue-50 text-blue-700 ring-blue-600/20",

  DUPLICATE:
    "bg-slate-100 text-slate-600 ring-slate-500/20",

  INVALID:
    "bg-red-50 text-red-700 ring-red-600/20",
};

export function LeadStatusBadge({
  status,
}: LeadStatusBadgeProps) {
  const style =
    statusStyles[status] ??
    "bg-slate-100 text-slate-700 ring-slate-500/20";

  return (
    <span
      className={[
        "inline-flex rounded-full px-2.5 py-1 text-xs font-semibold ring-1 ring-inset",
        style,
      ].join(" ")}
    >
      {status.replaceAll("_", " ")}
    </span>
  );
}