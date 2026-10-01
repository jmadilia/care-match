"use client";

import { useEffect, useState } from "react";
import {
  createClient,
  createSimulationRun,
  generateSimulationRun,
  getCandidates,
  listSimulationRuns,
  type Candidate,
  type SimulationRun,
} from "@/lib/api";
import { CandidateList } from "./CandidateList";
import { IntakeForm, type IntakeValues } from "./IntakeForm";

type LoadState = "loading" | "ready" | "error";

export default function IntakePage() {
  const [runs, setRuns] = useState<SimulationRun[]>([]);
  const [loadState, setLoadState] = useState<LoadState>("loading");
  const [creatingDemo, setCreatingDemo] = useState(false);
  const [submittedName, setSubmittedName] = useState<string | null>(null);
  const [candidates, setCandidates] = useState<Candidate[] | null>(null);
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function loadRuns() {
    setLoadState("loading");
    try {
      const fetched = await listSimulationRuns();
      setRuns(fetched);
      setLoadState("ready");
    } catch {
      setLoadState("error");
    }
  }

  useEffect(() => {
    // Fetch-once-on-mount: no external subscription to clean up here.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    void loadRuns();
  }, []);

  async function handleCreateDemo() {
    setCreatingDemo(true);
    setError(null);
    try {
      const run = await createSimulationRun({
        name: "Demo population",
        scenario: "balanced",
        seed: 1,
        provider_count: 20,
        client_count: 100,
      });
      await generateSimulationRun(run.id);
      await loadRuns();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not create a demo population.");
    } finally {
      setCreatingDemo(false);
    }
  }

  async function handleSubmit(values: IntakeValues) {
    setPending(true);
    setError(null);
    setCandidates(null);
    try {
      const client = await createClient({
        name: values.name,
        state: values.state,
        insurance_payer: values.insurancePayer,
        needed_specialties: values.neededSpecialties,
        preferred_modality: values.preferredModality,
        preferred_language: values.preferredLanguage,
        urgency: values.urgency,
        simulation_run_id: values.simulationRunId,
      });
      setSubmittedName(client.name);
      const found = await getCandidates(client.id, 5);
      setCandidates(found);
    } catch (err) {
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
        Submits a client against an existing simulation run&rsquo;s provider pool and ranks
        the result with the same scoring the matching strategies use.
      </p>

      <div className="mt-8 rounded-lg border p-6" style={{ borderColor: "var(--chart-gridline)" }}>
        {loadState === "loading" && (
          <p className="text-sm" style={{ color: "var(--chart-text-secondary)" }}>
            Loading simulation runs&hellip;
          </p>
        )}

        {loadState === "error" && (
          <p className="text-sm" style={{ color: "#d03b3b" }}>
            Could not reach the backend. Is it running at NEXT_PUBLIC_API_URL?
          </p>
        )}

        {loadState === "ready" && runs.length === 0 && (
          <div className="flex flex-col items-start gap-3">
            <p className="text-sm" style={{ color: "var(--chart-text-secondary)" }}>
              No simulation runs exist yet, so there is no provider pool to match against.
            </p>
            <button
              type="button"
              onClick={handleCreateDemo}
              disabled={creatingDemo}
              className="rounded-md px-4 py-2 text-sm font-medium text-white disabled:opacity-60"
              style={{ background: "var(--series-greedy)" }}
            >
              {creatingDemo ? "Generating…" : "Create a demo population"}
            </button>
          </div>
        )}

        {loadState === "ready" && runs.length > 0 && (
          <IntakeForm runs={runs} onSubmit={handleSubmit} pending={pending} />
        )}
      </div>

      {error && (
        <p className="mt-4 text-sm" style={{ color: "#d03b3b" }}>
          {error}
        </p>
      )}

      {candidates && (
        <div
          className="mt-8 flex flex-col gap-4 rounded-lg border p-6"
          style={{ borderColor: "var(--chart-gridline)" }}
        >
          <h2 className="text-sm font-medium" style={{ color: "var(--chart-text-primary)" }}>
            Candidates for {submittedName}
          </h2>
          <CandidateList candidates={candidates} />
        </div>
      )}
    </div>
  );
}
