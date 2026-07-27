"use client";

import {
  useActionState,
} from "react";

import {
  submitManualLead,
  type ManualEntryState,
} from "./actions";


const initialState:
  ManualEntryState = {
    success: false,
    error: null,

    status: null,
    intakeId: null,
    correlationId: null,

    duplicate: false,
    replayed: false,
  };


export function ManualLeadForm() {

  const [
    state,
    action,
    pending,
  ] =
    useActionState(
      submitManualLead,
      initialState,
    );

  return (
    <form
      action={action}
      className="rounded-xl border border-slate-200 bg-white p-6"
    >
      <div>
        <h2 className="text-lg font-semibold text-slate-950">
          Enter a lead
        </h2>

        <p className="mt-1 text-sm text-slate-500">
          The lead enters the same
          production intake and automation
          pipeline as every other source.
        </p>
      </div>

      <div className="mt-6 grid gap-5 md:grid-cols-2">

        <Field
          label="Full name"
          name="full_name"
          required
        />

        <Field
          label="Email"
          name="email"
          type="email"
        />

        <Field
          label="Phone"
          name="phone"
          placeholder="+12025550123"
        />

        <Select
          label="Service"
          name="service_type"
          required
          options={[
            [
              "plumbing",
              "Plumbing",
            ],
            [
              "electrical",
              "Electrical",
            ],
            [
              "hvac",
              "HVAC",
            ],
            [
              "appliance_repair",
              "Appliance repair",
            ],
            [
              "other",
              "Other",
            ],
          ]}
        />

        <Field
          label="Location"
          name="location"
          required
          placeholder="North District, 10021"
        />

        <Select
          label="Urgency"
          name="urgency"
          required
          options={[
            [
              "emergency",
              "Emergency",
            ],
            [
              "within_24_hours",
              "Within 24 hours",
            ],
            [
              "within_7_days",
              "Within 7 days",
            ],
            [
              "planning",
              "Planning",
            ],
            [
              "unknown",
              "Unknown",
            ],
          ]}
        />

        <Select
          label="Preferred contact"
          name="preferred_contact"
          options={[
            [
              "unknown",
              "Unknown",
            ],
            [
              "email",
              "Email",
            ],
            [
              "phone",
              "Phone",
            ],
            [
              "sms",
              "SMS",
            ],
          ]}
        />

      </div>

      <label className="mt-5 block">
        <span className="text-sm font-medium text-slate-700">
          Message
        </span>

        <textarea
          name="message"
          rows={4}
          maxLength={2000}
          className="mt-2 w-full resize-none rounded-lg border border-slate-300 px-3 py-2.5 text-sm outline-none focus:border-slate-500"
          placeholder="Describe the customer's request..."
        />
      </label>

      <label className="mt-5 flex items-start gap-3 rounded-lg bg-slate-50 p-4">

        <input
          type="checkbox"
          name="consent_marketing"
          className="mt-1"
        />

        <span>
          <span className="block text-sm font-medium text-slate-800">
            Marketing consent
          </span>

          <span className="mt-1 block text-xs leading-5 text-slate-500">
            Enable only when the customer
            explicitly consented to nurture
            communications.
          </span>
        </span>

      </label>

      {state.error ? (
        <div className="mt-5 rounded-lg bg-red-50 p-3 text-sm text-red-700">
          {state.error}
        </div>
      ) : null}

      {state.success ? (
        <div className="mt-5 rounded-lg bg-emerald-50 p-4 text-sm text-emerald-800">

          <div className="font-semibold">
            Lead accepted
          </div>

          <div className="mt-2">
            Status:{" "}
            <strong>
              {state.status}
            </strong>
          </div>

          <div className="mt-1 font-mono text-xs">
            Correlation ID:{" "}
            {state.correlationId}
          </div>

          {state.duplicate ? (
            <div className="mt-2">
              Existing lead detected and
              linked safely.
            </div>
          ) : null}

        </div>
      ) : null}

      <button
        type="submit"
        disabled={pending}
        className="mt-6 rounded-lg bg-slate-950 px-5 py-2.5 text-sm font-medium text-white disabled:cursor-not-allowed disabled:opacity-50"
      >
        {pending
          ? "Submitting..."
          : "Submit lead"}
      </button>
    </form>
  );
}


function Field({
  label,
  name,
  type = "text",
  required = false,
  placeholder,
}: {
  label: string;
  name: string;
  type?: string;
  required?: boolean;
  placeholder?: string;
}) {
  return (
    <label>
      <span className="text-sm font-medium text-slate-700">
        {label}
      </span>

      <input
        name={name}
        type={type}
        required={required}
        placeholder={placeholder}
        className="mt-2 w-full rounded-lg border border-slate-300 px-3 py-2.5 text-sm outline-none focus:border-slate-500"
      />
    </label>
  );
}


function Select({
  label,
  name,
  options,
  required = false,
}: {
  label: string;
  name: string;
  options: [
    string,
    string,
  ][];
  required?: boolean;
}) {
  return (
    <label>
      <span className="text-sm font-medium text-slate-700">
        {label}
      </span>

      <select
        name={name}
        required={required}
        defaultValue=""
        className="mt-2 w-full rounded-lg border border-slate-300 bg-white px-3 py-2.5 text-sm outline-none focus:border-slate-500"
      >
        {required ? (
          <option
            value=""
            disabled
          >
            Select
          </option>
        ) : null}

        {options.map(
          ([
            value,
            text,
          ]) => (
            <option
              key={value}
              value={value}
            >
              {text}
            </option>
          ),
        )}
      </select>
    </label>
  );
}