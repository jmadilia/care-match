// 127.0.0.1 (not "localhost") avoids Node's fetch trying an IPv6 route to a
// backend that only listens on IPv4.
export const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";

export type Scenario = "balanced" | "undersupplied_state" | "scarce_specialty";

export type UrgencyTier = "ROUTINE" | "ELEVATED" | "URGENT";

export type StrategyRunSummary = {
  strategy: string;
  client_count: number;
  matched_count: number;
  unmatched_count: number;
  fill_rate: number;
  mean_match_score: number;
  provider_utilization_std: number;
  fill_rate_by_urgency: Partial<Record<UrgencyTier, number>>;
};

export type SeededStrategyRun = StrategyRunSummary & { seed: number };

export type StrategyAggregate = {
  strategy: string;
  runs: number;
  mean_fill_rate: number;
  std_fill_rate: number;
  mean_match_score_mean: number;
  mean_match_score_std: number;
  mean_provider_utilization_std: number;
  mean_fill_rate_by_urgency: Partial<Record<UrgencyTier, number>>;
};

export type ComparisonRequest = {
  scenario: Scenario;
  seeds: number[];
  provider_count: number;
  client_count: number;
};

export type ComparisonResult = {
  scenario: Scenario;
  seeds: number[];
  provider_count: number;
  client_count: number;
  per_seed: SeededStrategyRun[];
  aggregates: StrategyAggregate[];
};

export async function runComparison(request: ComparisonRequest): Promise<ComparisonResult> {
  const res = await fetch(`${API_URL}/api/v1/comparisons`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(request),
  });
  if (!res.ok) {
    throw new Error(await describeApiError(res, "Comparison"));
  }
  return res.json();
}

// FastAPI validation failures arrive as { detail: [{ msg }] }; show the messages
// instead of the raw JSON.
async function describeApiError(res: Response, what: string): Promise<string> {
  const text = await res.text();
  try {
    const body = JSON.parse(text);
    if (Array.isArray(body.detail)) {
      const messages = body.detail.map((d: { msg: string }) => d.msg).join("; ");
      return `${what} rejected: ${messages}`;
    }
  } catch {
    // Not JSON, fall through to the raw text.
  }
  return `${what} failed (${res.status}): ${text}`;
}

export type Provider = {
  id: string;
  name: string;
  license_states: string[];
  specialties: string[];
  modalities: string[];
  languages: string[];
  insurance_panels: string[];
  weekly_capacity: number;
};

export type Candidate = {
  provider: Provider;
  score: number;
  remaining_capacity: number;
};

export type IntakeRequest = {
  scenario: Scenario;
  seed: number;
  state: string;
  insurance_payer: string;
  needed_specialties: string[];
  preferred_modality: string;
  preferred_language: string;
  limit?: number;
};

export type IntakeResult = {
  scenario: Scenario;
  seed: number;
  pool_provider_count: number;
  candidates: Candidate[];
};

// Stateless: the backend regenerates the provider pool from (scenario, seed), ranks it for
// these answers, and discards it. Nothing is stored.
export async function findIntakeCandidates(request: IntakeRequest): Promise<IntakeResult> {
  const res = await fetch(`${API_URL}/api/v1/intake`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(request),
  });
  if (!res.ok) {
    throw new Error(await describeApiError(res, "Intake"));
  }
  return res.json();
}
