import { LoginForm } from "./login-form";

export default function LoginPage() {
  return (
    <main className="flex min-h-screen items-center justify-center bg-slate-100 px-6">
      <div className="w-full max-w-md rounded-2xl border border-slate-200 bg-white p-8 shadow-sm">
        <div className="mb-2 text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">
          LeadFlow AI
        </div>

        <h1 className="text-3xl font-semibold tracking-tight text-slate-950">
          Operations Console
        </h1>

        <p className="mt-3 text-sm leading-6 text-slate-600">
          Sign in to manage leads,
          review automation decisions,
          and monitor workflow health.
        </p>

        <LoginForm />
      </div>
    </main>
  );
}