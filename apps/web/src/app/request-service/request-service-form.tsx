"use client";

import { useActionState } from "react";
import {
  submitServiceRequest,
  type ServiceRequestState,
} from "./actions";

const initialState: ServiceRequestState = {
  success: false,
  error: null,
  leadId: null,
};

export function RequestServiceForm() {
  const [state, action, pending] = useActionState(
    submitServiceRequest,
    initialState,
  );

  if (state.success) {
    return (
      <div className="rounded-2xl border border-emerald-200 bg-emerald-50 p-8">
        <p className="text-sm font-semibold text-emerald-700">Request received</p>
        <h2 className="mt-3 text-2xl font-semibold text-slate-950">
          We have your service request.
        </h2>
        <p className="mt-3 text-slate-600">
          The appropriate NorthStar team will review it and follow up.
        </p>
        {state.leadId ? (
          <p className="mt-4 font-mono text-xs text-slate-500">
            Ref: {state.leadId.slice(0, 8)}
          </p>
        ) : null}
      </div>
    );
  }

  return (
    <form action={action} className="rounded-2xl border border-slate-200 bg-white p-7 shadow-sm">
      <h2 className="text-2xl font-semibold text-slate-950">Request service</h2>
      <div className="mt-6 grid gap-5 md:grid-cols-2">
        <Field label="Full name" name="full_name" required />
        <Field label="Email" name="email" type="email" />
        <Field label="Phone" name="phone" />
        <Select
          label="Service"
          name="service_type"
          options={[
            ["plumbing", "Plumbing"],
            ["electrical", "Electrical"],
            ["hvac", "Heating & cooling"],
            ["appliance_repair", "Appliance repair"],
            ["other", "Other / not sure"],
          ]}
        />
        <Field label="Location" name="location" required />
        <Select
          label="Urgency"
          name="urgency"
          options={[
            ["emergency", "Emergency"],
            ["within_24_hours", "Within 24 hours"],
            ["within_7_days", "Within 7 days"],
            ["planning", "Planning"],
            ["unknown", "Not sure"],
          ]}
        />
        <Select
          label="Preferred contact"
          name="preferred_contact"
          options={[
            ["email", "Email"],
            ["phone", "Phone"],
            ["sms", "SMS"],
            ["unknown", "No preference"],
          ]}
        />
      </div>

      <label className="mt-5 block text-sm font-medium text-slate-700">
        What do you need help with?
        <textarea
          name="message"
          rows={5}
          maxLength={2000}
          className="mt-2 w-full rounded-xl border border-slate-300 px-3 py-3"
        />
      </label>

      <label className="mt-5 flex gap-3 rounded-xl bg-slate-50 p-4 text-xs text-slate-500">
        <input type="checkbox" name="consent_marketing" className="mt-1" />
        I agree to optional service reminders and promotional updates.
      </label>

      {state.error ? (
        <div className="mt-5 rounded-xl bg-red-50 p-3 text-sm text-red-700">
          {state.error}
        </div>
      ) : null}

      <button
        type="submit"
        disabled={pending}
        className="mt-6 w-full rounded-xl bg-blue-700 px-5 py-3 text-sm font-semibold text-white disabled:opacity-50"
      >
        {pending ? "Sending..." : "Request service"}
      </button>
    </form>
  );
}

function Field({
  label,
  name,
  type = "text",
  required = false,
}: {
  label: string;
  name: string;
  type?: string;
  required?: boolean;
}) {
  return (
    <label className="text-sm font-medium text-slate-700">
      {label}
      <input
        name={name}
        type={type}
        required={required}
        className="mt-2 w-full rounded-xl border border-slate-300 px-3 py-3"
      />
    </label>
  );
}

function Select({
  label,
  name,
  options,
}: {
  label: string;
  name: string;
  options: [string, string][];
}) {
  return (
    <label className="text-sm font-medium text-slate-700">
      {label}
      <select
        name={name}
        required
        defaultValue=""
        className="mt-2 w-full rounded-xl border border-slate-300 bg-white px-3 py-3"
      >
        <option value="" disabled>
          Select
        </option>
        {options.map(([value, text]) => (
          <option key={value} value={value}>
            {text}
          </option>
        ))}
      </select>
    </label>
  );
}
