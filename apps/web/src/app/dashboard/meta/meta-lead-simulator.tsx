"use client";

import { useActionState } from "react";
import { simulateMetaLead, type MetaSimulatorState } from "./actions";

const initialState: MetaSimulatorState = {
  success: false,
  error: null,
  status: null,
  outcome: null,
  eventId: null,
};

export function MetaLeadSimulator() {
  const [state, action, pending] = useActionState(simulateMetaLead, initialState);

  return (
    <form action={action} className="rounded-xl border border-slate-200 bg-white p-6">
      <h2 className="text-lg font-semibold text-slate-950">
        Generate a synthetic Meta lead
      </h2>
      <p className="mt-2 text-sm text-slate-500">
        Portfolio simulator only. It represents a canonicalized Meta lead
        entering the production n8n workflow; it does not connect to a real ad account.
      </p>

      <div className="mt-6 grid gap-5 md:grid-cols-2">
        <Field label="Lead name" name="full_name" defaultValue="Olivia Bennett" />
        <Field
          label="Email"
          name="email"
          type="email"
          defaultValue="delivered+leadflow-meta01@resend.dev"
        />
        <Field label="Phone" name="phone" defaultValue="+12025553187" />
        <Field
          label="Campaign"
          name="campaign_name"
          defaultValue="NorthStar Summer Service Leads"
        />

        <Select
          label="Service"
          name="service_type"
          defaultValue="electrical"
          options={[
            ["plumbing", "Plumbing"],
            ["electrical", "Electrical"],
            ["hvac", "HVAC"],
            ["appliance_repair", "Appliance repair"],
            ["other", "Other"],
          ]}
        />

        <Field
          label="Location"
          name="location"
          defaultValue="North District, 10021"
        />

        <Select
          label="Urgency"
          name="urgency"
          defaultValue="within_7_days"
          options={[
            ["emergency", "Emergency"],
            ["within_24_hours", "Within 24 hours"],
            ["within_7_days", "Within 7 days"],
            ["planning", "Planning"],
            ["unknown", "Unknown"],
          ]}
        />
      </div>

      <label className="mt-5 block text-sm font-medium text-slate-700">
        Lead message
        <textarea
          name="message"
          rows={4}
          defaultValue="Several outlets stopped working and I would like an electrician to inspect the circuit this week."
          className="mt-2 w-full rounded-lg border border-slate-300 px-3 py-2.5"
        />
      </label>

      <label className="mt-5 flex gap-3 rounded-lg bg-slate-50 p-4 text-sm text-slate-600">
        <input type="checkbox" name="consent_marketing" defaultChecked />
        Simulated Meta marketing consent
      </label>

      {state.error ? (
        <div className="mt-5 rounded-lg bg-red-50 p-3 text-sm text-red-700">
          {state.error}
        </div>
      ) : null}

      {state.success ? (
        <div className="mt-5 rounded-lg bg-emerald-50 p-4 text-sm text-emerald-800">
          <div className="font-semibold">Meta lead accepted.</div>
          <div className="mt-2">Status: {state.status ?? "—"}</div>
          <div>Workflow: {state.outcome ?? "—"}</div>
          <div className="mt-1 font-mono text-xs">Event: {state.eventId}</div>
        </div>
      ) : null}

      <button
        type="submit"
        disabled={pending}
        className="mt-6 rounded-lg bg-slate-950 px-5 py-2.5 text-sm font-medium text-white disabled:opacity-50"
      >
        {pending ? "Sending..." : "Simulate Meta lead"}
      </button>
    </form>
  );
}

function Field({
  label,
  name,
  type = "text",
  defaultValue,
}: {
  label: string;
  name: string;
  type?: string;
  defaultValue?: string;
}) {
  return (
    <label className="text-sm font-medium text-slate-700">
      {label}
      <input
        name={name}
        type={type}
        required
        defaultValue={defaultValue}
        className="mt-2 w-full rounded-lg border border-slate-300 px-3 py-2.5"
      />
    </label>
  );
}

function Select({
  label,
  name,
  options,
  defaultValue,
}: {
  label: string;
  name: string;
  options: [string, string][];
  defaultValue: string;
}) {
  return (
    <label className="text-sm font-medium text-slate-700">
      {label}
      <select
        name={name}
        required
        defaultValue={defaultValue}
        className="mt-2 w-full rounded-lg border border-slate-300 bg-white px-3 py-2.5"
      >
        {options.map(([value, text]) => (
          <option key={value} value={value}>
            {text}
          </option>
        ))}
      </select>
    </label>
  );
}
