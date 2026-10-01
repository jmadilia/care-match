"use client";

import { useId, useState } from "react";
import type { Scenario } from "@/lib/api";

export type ComparisonFormValues = {
  scenario: Scenario;
  seedCount: number;
  providerCount: number;
  clientCount: number;
};

const SCENARIOS: { value: Scenario; label: string }[] = [
  { value: "balanced", label: "Balanced" },
  { value: "undersupplied_state", label: "Undersupplied state" },
  { value: "scarce_specialty", label: "Scarce specialty" },
];

const inputClass =
  "w-full rounded-md border px-3 py-2 text-sm outline-none focus-visible:ring-2";
const inputStyle = {
  background: "var(--chart-surface)",
  borderColor: "var(--chart-gridline)",
  color: "var(--chart-text-primary)",
};

export function ComparisonForm({
  onSubmit,
  pending,
}: {
  onSubmit: (values: ComparisonFormValues) => void;
  pending: boolean;
}) {
  const [scenario, setScenario] = useState<Scenario>("balanced");
  const [seedCount, setSeedCount] = useState(10);
  const [providerCount, setProviderCount] = useState(60);
  const [clientCount, setClientCount] = useState(300);
  const scenarioId = useId();
  const seedsId = useId();
  const providersId = useId();
  const clientsId = useId();

  return (
    <form
      className="flex flex-wrap items-end gap-4"
      onSubmit={(e) => {
        e.preventDefault();
        onSubmit({ scenario, seedCount, providerCount, clientCount });
      }}
    >
      <div className="flex flex-col gap-1">
        <label htmlFor={scenarioId} className="text-xs" style={{ color: "var(--chart-text-secondary)" }}>
          Scenario
        </label>
        <select
          id={scenarioId}
          className={inputClass}
          style={inputStyle}
          value={scenario}
          onChange={(e) => setScenario(e.target.value as Scenario)}
        >
          {SCENARIOS.map((s) => (
            <option key={s.value} value={s.value}>
              {s.label}
            </option>
          ))}
        </select>
      </div>

      <div className="flex flex-col gap-1">
        <label htmlFor={seedsId} className="text-xs" style={{ color: "var(--chart-text-secondary)" }}>
          Seeds
        </label>
        <input
          id={seedsId}
          type="number"
          min={1}
          max={50}
          className={`${inputClass} w-24`}
          style={inputStyle}
          value={seedCount}
          onChange={(e) => setSeedCount(Number(e.target.value))}
        />
      </div>

      <div className="flex flex-col gap-1">
        <label htmlFor={providersId} className="text-xs" style={{ color: "var(--chart-text-secondary)" }}>
          Providers
        </label>
        <input
          id={providersId}
          type="number"
          min={1}
          className={`${inputClass} w-28`}
          style={inputStyle}
          value={providerCount}
          onChange={(e) => setProviderCount(Number(e.target.value))}
        />
      </div>

      <div className="flex flex-col gap-1">
        <label htmlFor={clientsId} className="text-xs" style={{ color: "var(--chart-text-secondary)" }}>
          Clients
        </label>
        <input
          id={clientsId}
          type="number"
          min={1}
          className={`${inputClass} w-28`}
          style={inputStyle}
          value={clientCount}
          onChange={(e) => setClientCount(Number(e.target.value))}
        />
      </div>

      <button
        type="submit"
        disabled={pending}
        className="rounded-md px-4 py-2 text-sm font-medium text-white disabled:opacity-60"
        style={{ background: "var(--series-greedy)" }}
      >
        {pending ? "Running…" : "Run comparison"}
      </button>
    </form>
  );
}
