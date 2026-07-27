import {
  CsvImportForm,
} from "./csv-import-form";

import {
  ManualLeadForm,
} from "./manual-lead-form";


export default function
ManualEntryPage() {

  return (
    <div className="space-y-7">

      <div>
        <p className="text-sm font-medium text-slate-500">
          Intake
        </p>

        <h1 className="mt-1 text-3xl font-semibold text-slate-950">
          Manual Lead Entry
        </h1>

        <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-600">
          Submit individual leads or synthetic
          CSV batches into the same LeadFlow
          intake pipeline used by external
          sources.
        </p>
      </div>

      <div className="grid gap-6 xl:grid-cols-[1.15fr_0.85fr]">

        <ManualLeadForm />

        <CsvImportForm />

      </div>

    </div>
  );
}