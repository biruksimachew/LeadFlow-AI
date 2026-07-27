import Link from "next/link";
import { RequestServiceForm } from "./request-service-form";

export default function RequestServicePage() {
  return (
    <main className="min-h-screen bg-slate-50">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-5">
          <Link href="/" className="text-lg font-semibold text-slate-950">
            NorthStar Home Services
          </Link>
          <Link href="/login" className="text-sm text-slate-500">
            Staff sign in
          </Link>
        </div>
      </header>

      <section className="mx-auto grid max-w-6xl gap-10 px-6 py-14 lg:grid-cols-[0.8fr_1.2fr]">
        <div className="lg:pt-10">
          <p className="text-sm font-semibold uppercase tracking-[0.2em] text-blue-700">
            NorthStar Home Services
          </p>
          <h1 className="mt-4 text-4xl font-semibold tracking-tight text-slate-950 sm:text-5xl">
            Get the right service team without the runaround.
          </h1>
          <p className="mt-5 text-base leading-8 text-slate-600">
            Tell us what is happening and when you need help. We will route
            your request to the right team.
          </p>
        </div>

        <RequestServiceForm />
      </section>
    </main>
  );
}
