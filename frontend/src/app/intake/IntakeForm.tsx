"use client";

import { useId, useState } from "react";
import type { SimulationRun, UrgencyTier } from "@/lib/api";
import { LANGUAGES, MODALITIES, PAYERS, SPECIALTIES, STATES } from "./vocabulary";

export type IntakeValues = {
  name: string;
  state: string;
  insurancePayer: string;
  neededSpecialties: string[];
  preferredModality: string;
  preferredLanguage: string;
  urgency: UrgencyTier;
  simulationRunId: string;
};

const inputClass = "w-full rounded-md border px-3 py-2 text-sm outline-none focus-visible:ring-2";
const inputStyle = {
  background: "var(--chart-surface)",
  borderColor: "var(--chart-gridline)",
  color: "var(--chart-text-primary)",
};
const labelClass = "text-xs";
const labelStyle = { color: "var(--chart-text-secondary)" };

export function IntakeForm({
  runs,
  onSubmit,
  pending,
}: {
  runs: SimulationRun[];
  onSubmit: (values: IntakeValues) => void;
  pending: boolean;
}) {
  const [name, setName] = useState("");
  const [state, setState] = useState<string>(STATES[0]);
  const [insurancePayer, setInsurancePayer] = useState<string>(PAYERS[0]);
  const [neededSpecialties, setNeededSpecialties] = useState<string[]>([SPECIALTIES[0]]);
  const [preferredModality, setPreferredModality] = useState<string>(MODALITIES[0]);
  const [preferredLanguage, setPreferredLanguage] = useState<string>(LANGUAGES[0]);
  const [urgency, setUrgency] = useState<UrgencyTier>("ROUTINE");
  const [simulationRunId, setSimulationRunId] = useState(runs[0]?.id ?? "");

  const nameId = useId();
  const stateId = useId();
  const payerId = useId();
  const modalityId = useId();
  const languageId = useId();
  const urgencyId = useId();
  const runId = useId();

  function toggleSpecialty(specialty: string) {
    setNeededSpecialties((current) =>
      current.includes(specialty)
        ? current.filter((s) => s !== specialty)
        : [...current, specialty],
    );
  }

  return (
    <form
      className="flex flex-col gap-4"
      onSubmit={(e) => {
        e.preventDefault();
        if (!name.trim() || neededSpecialties.length === 0 || !simulationRunId) return;
        onSubmit({
          name,
          state,
          insurancePayer,
          neededSpecialties,
          preferredModality,
          preferredLanguage,
          urgency,
          simulationRunId,
        });
      }}
    >
      <div className="flex flex-col gap-1">
        <label htmlFor={runId} className={labelClass} style={labelStyle}>
          Match against provider pool from
        </label>
        <select
          id={runId}
          className={inputClass}
          style={inputStyle}
          value={simulationRunId}
          onChange={(e) => setSimulationRunId(e.target.value)}
        >
          {runs.map((run) => (
            <option key={run.id} value={run.id}>
              {run.name} ({run.provider_count} providers, {run.scenario})
            </option>
          ))}
        </select>
      </div>

      <div className="flex flex-col gap-1">
        <label htmlFor={nameId} className={labelClass} style={labelStyle}>
          Name
        </label>
        <input
          id={nameId}
          className={inputClass}
          style={inputStyle}
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="Jane Doe"
          required
        />
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div className="flex flex-col gap-1">
          <label htmlFor={stateId} className={labelClass} style={labelStyle}>
            State
          </label>
          <select
            id={stateId}
            className={inputClass}
            style={inputStyle}
            value={state}
            onChange={(e) => setState(e.target.value)}
          >
            {STATES.map((s) => (
              <option key={s} value={s}>
                {s}
              </option>
            ))}
          </select>
        </div>

        <div className="flex flex-col gap-1">
          <label htmlFor={payerId} className={labelClass} style={labelStyle}>
            Insurance
          </label>
          <select
            id={payerId}
            className={inputClass}
            style={inputStyle}
            value={insurancePayer}
            onChange={(e) => setInsurancePayer(e.target.value)}
          >
            {PAYERS.map((p) => (
              <option key={p} value={p}>
                {p}
              </option>
            ))}
          </select>
        </div>
      </div>

      <fieldset className="flex flex-col gap-1">
        <legend className={labelClass} style={labelStyle}>
          Needed specialties
        </legend>
        <div className="flex flex-wrap gap-x-4 gap-y-2 pt-1">
          {SPECIALTIES.map((specialty) => (
            <label
              key={specialty}
              className="flex items-center gap-1.5 text-sm"
              style={{ color: "var(--chart-text-primary)" }}
            >
              <input
                type="checkbox"
                checked={neededSpecialties.includes(specialty)}
                onChange={() => toggleSpecialty(specialty)}
              />
              {specialty.replace("_", " ")}
            </label>
          ))}
        </div>
      </fieldset>

      <div className="grid grid-cols-3 gap-4">
        <div className="flex flex-col gap-1">
          <label htmlFor={modalityId} className={labelClass} style={labelStyle}>
            Modality
          </label>
          <select
            id={modalityId}
            className={inputClass}
            style={inputStyle}
            value={preferredModality}
            onChange={(e) => setPreferredModality(e.target.value)}
          >
            {MODALITIES.map((m) => (
              <option key={m} value={m}>
                {m.replace("_", " ")}
              </option>
            ))}
          </select>
        </div>

        <div className="flex flex-col gap-1">
          <label htmlFor={languageId} className={labelClass} style={labelStyle}>
            Language
          </label>
          <select
            id={languageId}
            className={inputClass}
            style={inputStyle}
            value={preferredLanguage}
            onChange={(e) => setPreferredLanguage(e.target.value)}
          >
            {LANGUAGES.map((l) => (
              <option key={l} value={l}>
                {l}
              </option>
            ))}
          </select>
        </div>

        <div className="flex flex-col gap-1">
          <label htmlFor={urgencyId} className={labelClass} style={labelStyle}>
            Urgency
          </label>
          <select
            id={urgencyId}
            className={inputClass}
            style={inputStyle}
            value={urgency}
            onChange={(e) => setUrgency(e.target.value as UrgencyTier)}
          >
            <option value="ROUTINE">Routine</option>
            <option value="ELEVATED">Elevated</option>
            <option value="URGENT">Urgent</option>
          </select>
        </div>
      </div>

      <button
        type="submit"
        disabled={pending || neededSpecialties.length === 0}
        className="self-start rounded-md px-4 py-2 text-sm font-medium text-white disabled:opacity-60"
        style={{ background: "var(--series-greedy)" }}
      >
        {pending ? "Finding candidates…" : "Find providers"}
      </button>
    </form>
  );
}
