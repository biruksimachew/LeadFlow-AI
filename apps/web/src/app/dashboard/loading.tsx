export default function DashboardLoading() {
  return (
    <div
      aria-label="Loading dashboard"
      className="animate-pulse"
    >
      <div className="h-4 w-36 rounded bg-slate-200" />
      <div className="mt-3 h-9 w-64 rounded bg-slate-200" />
      <div className="mt-3 h-4 w-96 max-w-full rounded bg-slate-200" />

      <div className="mt-8 grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
        {Array.from(
          {
            length: 6,
          },
        ).map(
          (_, index) => (
            <div
              key={index}
              className="h-36 rounded-xl border border-slate-200 bg-white"
            />
          ),
        )}
      </div>

      <div className="mt-8 h-48 rounded-xl border border-slate-200 bg-white" />

      <div className="mt-8 grid gap-6 xl:grid-cols-2">
        {Array.from(
          {
            length: 4,
          },
        ).map(
          (_, index) => (
            <div
              key={index}
              className="h-72 rounded-xl border border-slate-200 bg-white"
            />
          ),
        )}
      </div>
    </div>
  );
}
