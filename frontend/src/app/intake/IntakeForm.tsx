"use client";

import { useId, useState } from "react";
import type { Scenario } from "@/lib/api";
import { LANGUAGES, MODALITIES, PAYERS, SPECIALTIES, STATES } from "./vocabulary";

export type IntakeValues = {
  scenario: Scenario;
  seed: number;
  state: string;
  insurancePayer: string;
  neededSpecialties: string[];
  preferredModality: string;
  preferredLanguage: string;
};

const SCENARIOS: { value: Scenario; label: string }[] = [
  { value: "balanced", label: "Balanced" },
  { value: "undersupplied_state", label: "Undersupplied state" },
  { value: "scarce_specialty", label: "Scarce specialty" },
];

const MAX_SEED = 100000;

const inputClass = "w-full rounded-md border px-3 py-2 text-sm outline-none focus-visible:ring-2";
const inputStyle = {
  background: "var(--chart-surface)",
  borderColor: "var(--chart-gridline)",
  color: "var(--chart-text-primary)",
};
const labelClass = "text-xs";
const labelStyle = { color: "var(--chart-text-secondary)" };

export function IntakeForm({
  onSubmit,
  pending,
}: {
  onSubmit: (values: IntakeValues) => void;
  pending: boolean;
}) {
  const [scenario, setScenario] = useState<Scenario>("balanced");
  const [seed, setSeed] = useState(1);
  const [state, setState] = useState<string>(STATES[0]);
  const [insurancePayer, setInsurancePayer] = useState<string>(PAYERS[0]);
  const [neededSpecialties, setNeededSpecialties] = useState<string[]>([SPECIALTIES[0]]);
  const [preferredModality, setPreferredModality] = useState<string>(MODALITIES[0]);
  const [preferredLanguage, setPreferredLanguage] = useState<string>(LANGUAGES[0]);

  const scenarioId = useId();
  const seedId = useId();
  const stateId = useId();
  const payerId = useId();
  const modalityId = useId();
  const languageId = useId();

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
        if (neededSpecialties.length === 0) return;
        onSubmit({
          scenario,
          seed,
          state,
          insurancePayer,
          neededSpecialties,
          preferredModality,
          preferredLanguage,
        });
      }}
    >
      <div className="grid grid-cols-2 gap-4">
        <div className="flex flex-col gap-1">
          <label htmlFor={scenarioId} className={labelClass} style={labelStyle}>
            Provider pool scenario
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
          <label htmlFor={seedId} className={labelClass} style={labelStyle}>
            Pool seed
          </label>
          <input
            id={seedId}
            type="number"
            min={0}
            max={MAX_SEED}
            className={inputClass}
            style={inputStyle}
            value={seed}
            onChange={(e) => setSeed(Number(e.target.value))}
          />
        </div>
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

      <div className="grid grid-cols-2 gap-4">
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
