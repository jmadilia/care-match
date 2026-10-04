"use client";

import { useState } from "react";
import { findIntakeCandidates, type IntakeResult } from "@/lib/api";
import { CandidateList } from "./CandidateList";
import { IntakeForm, type IntakeValues } from "./IntakeForm";

const SCENARIO_LABELS = {
  balanced: "balanced",
  undersupplied_state: "undersupplied state",
  scarce_specialty: "scarce specialty",
} as const;

export default function IntakePage() {
  const [result, setResult] = useState<IntakeResult | null>(null);
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(values: IntakeValues) {
    setPending(true);
    setError(null);
    try {
      const next = await findIntakeCandidates({
        scenario: values.scenario,
        seed: values.seed,
        state: values.state,
        insurance_payer: values.insurancePayer,
        needed_specialties: values.neededSpecialties,
        preferred_modality: values.preferredModality,
        preferred_language: values.preferredLanguage,
      });
      setResult(next);
    } catch (err) {
      setResult(null);
      setError(err instanceof Error ? err.message : "Something went wrong.");
    } finally {
      setPending(false);
    }
  }

  return (
    <div className="mx-auto w-full max-w-2xl px-6 py-12">
      <h1 className="text-2xl font-semibold" style={{ color: "var(--chart-text-primary)" }}>
        Client intake
      </h1>
      <p className="mt-2 text-sm" style={{ color: "var(--chart-text-secondary)" }}>
        Generates a provider pool from a scenario and seed, ranks it for your answers with the
        same scoring the matching strategies use, then discards it. Nothing you enter is stored,
        and no name is collected. The same seed always produces the same pool.
      </p>

      <div className="mt-8 rounded-lg border p-6" style={{ borderColor: "var(--chart-gridline)" }}>
        <IntakeForm onSubmit={handleSubmit} pending={pending} />
      </div>

      {error && (
        <p className="mt-4 text-sm" style={{ color: "#d03b3b" }}>
          {error}
        </p>
      )}

      {result && (
        <div
          className="mt-8 flex flex-col gap-4 rounded-lg border p-6"
          style={{ borderColor: "var(--chart-gridline)", opacity: pending ? 0.6 : 1 }}
        >
          <h2 className="text-sm font-medium" style={{ color: "var(--chart-text-primary)" }}>
            Top matches from a {SCENARIO_LABELS[result.scenario]} pool of{" "}
            {result.pool_provider_count} providers (seed {result.seed})
          </h2>
          <CandidateList candidates={result.candidates} />
        </div>
      )}
    </div>
  );
}
