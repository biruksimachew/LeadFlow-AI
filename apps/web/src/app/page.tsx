import Link from "next/link";

export default function HomePage() {
  return (
    <main className="min-h-screen bg-white">
      <header className="border-b border-slate-200">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-5">
          <div className="text-lg font-semibold text-slate-950">
            NorthStar Home Services
          </div>
          <div className="flex items-center gap-4">
            <Link href="/login" className="text-sm text-slate-500">
              Staff sign in
            </Link>
            <Link
              href="/request-service"
              className="rounded-lg bg-blue-700 px-4 py-2 text-sm font-semibold text-white"
            >
              Request service
            </Link>
          </div>
        </div>
      </header>

      <section className="bg-slate-950 text-white">
        <div className="mx-auto grid max-w-6xl gap-12 px-6 py-24 lg:grid-cols-2">
          <div>
            <p className="text-sm font-semibold uppercase tracking-[0.2em] text-blue-300">
              Reliable home-service support
            </p>
            <h1 className="mt-5 text-5xl font-semibold tracking-tight sm:text-6xl">
              One request. The right team. Faster follow-up.
            </h1>
            <p className="mt-6 max-w-2xl text-lg leading-8 text-slate-300">
              Plumbing, electrical, HVAC and appliance service requests,
              routed to the right team with a responsive customer experience.
            </p>
            <Link
              href="/request-service"
              className="mt-8 inline-block rounded-xl bg-blue-600 px-5 py-3 text-sm font-semibold"
            >
              Request service
            </Link>
          </div>

          <div className="rounded-3xl border border-slate-800 bg-slate-900 p-8">
            <p className="text-sm font-semibold text-blue-300">What happens next</p>
            <div className="mt-6 space-y-5 text-sm text-slate-200">
              <p>01 — Tell us what you need</p>
              <p>02 — We route the request</p>
              <p>03 — The right team follows up</p>
            </div>
          </div>
        </div>
      </section>

      <section className="mx-auto max-w-6xl px-6 py-16">
        <h2 className="text-3xl font-semibold text-slate-950">Services</h2>
        <div className="mt-8 grid gap-4 md:grid-cols-2">
          {["Plumbing", "Electrical", "Heating & cooling", "Appliance repair"].map(
            (service) => (
              <div key={service} className="rounded-2xl border border-slate-200 p-6">
                <h3 className="font-semibold text-slate-950">{service}</h3>
                <p className="mt-2 text-sm text-slate-500">
                  Fast intake, smart routing and clear follow-up.
                </p>
              </div>
            ),
          )}
        </div>
      </section>
    </main>
  );
}
