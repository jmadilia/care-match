"use client";

import { useState } from "react";
import { runComparison, type ComparisonResult } from "@/lib/api";
import { ComparisonForm, type ComparisonFormValues } from "./ComparisonForm";
import { FillRateChart } from "./FillRateChart";
import { ResultsTable } from "./ResultsTable";
import { StrategyLegend } from "./StrategyLegend";
import { UrgencyChart } from "./UrgencyChart";

export default function ComparisonsPage() {
  const [result, setResult] = useState<ComparisonResult | null>(null);
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(values: ComparisonFormValues) {
    setPending(true);
    setError(null);
    try {
      const seeds = Array.from({ length: values.seedCount }, (_, i) => i + 1);
      const next = await runComparison({
        scenario: values.scenario,
        seeds,
        provider_count: values.providerCount,
        client_count: values.clientCount,
      });
      setResult(next);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong.");
    } finally {
      setPending(false);
    }
  }

  return (
    <div className="mx-auto w-full max-w-4xl px-6 py-12">
      <h1 className="text-2xl font-semibold" style={{ color: "var(--chart-text-primary)" }}>
        Strategy comparison
      </h1>
      <p className="mt-2 text-sm" style={{ color: "var(--chart-text-secondary)" }}>
        Runs greedy, stable matching, optimal assignment, and waitlist priority against the
        same generated population for each seed, then reports fill rate, match score, provider
        utilization, and fill rate by urgency tier, averaged across seeds.
      </p>

      <div className="mt-8 rounded-lg border p-4" style={{ borderColor: "var(--chart-gridline)" }}>
        <ComparisonForm onSubmit={handleSubmit} pending={pending} />
      </div>

      {error && (
        <p className="mt-4 text-sm" style={{ color: "#d03b3b" }}>
          {error}
        </p>
      )}

      {result && (
        <div
          className="mt-8 flex flex-col gap-10 rounded-lg border p-6"
          style={{ borderColor: "var(--chart-gridline)", opacity: pending ? 0.6 : 1 }}
        >
          <StrategyLegend />
          <FillRateChart aggregates={result.aggregates} />
          <UrgencyChart aggregates={result.aggregates} />
          <ResultsTable aggregates={result.aggregates} />
          <p className="text-xs" style={{ color: "var(--chart-text-muted)" }}>
            {result.scenario} scenario · {result.provider_count} providers ·{" "}
            {result.client_count} clients · {result.seeds.length} seeds
          </p>
        </div>
      )}
    </div>
  );
}
