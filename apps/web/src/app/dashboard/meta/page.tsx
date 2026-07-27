import { MetaLeadSimulator } from "./meta-lead-simulator";

export default function MetaSimulatorPage() {
  return (
    <div className="space-y-6">
      <div>
        <p className="text-sm font-medium text-slate-500">Lead Sources</p>
        <h1 className="mt-1 text-3xl font-semibold text-slate-950">
          Meta Lead Ads Simulator
        </h1>
        <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-600">
          Generate synthetic Meta leads and send them through the same
          production n8n orchestration used by website requests.
        </p>
      </div>

      <MetaLeadSimulator />
    </div>
  );
}
