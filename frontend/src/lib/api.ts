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
    const detail = await res.text();
    throw new Error(`Comparison failed (${res.status}): ${detail}`);
  }
  return res.json();
}

export type Client = {
  id: string;
  name: string;
  state: string;
  insurance_payer: string;
  needed_specialties: string[];
  preferred_modality: string;
  preferred_language: string;
  urgency: UrgencyTier;
  arrival_day: number | null;
  simulation_run_id: string | null;
  created_at: string;
};

export type ClientCreate = {
  name: string;
  state: string;
  insurance_payer: string;
  needed_specialties: string[];
  preferred_modality: string;
  preferred_language: string;
  urgency?: UrgencyTier;
  simulation_run_id?: string | null;
};

export async function createClient(input: ClientCreate): Promise<Client> {
  const res = await fetch(`${API_URL}/api/v1/clients`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input),
  });
  if (!res.ok) {
    const detail = await res.text();
    throw new Error(`Failed to create client (${res.status}): ${detail}`);
  }
  return res.json();
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
  simulation_run_id: string | null;
  created_at: string;
};

export type Candidate = {
  provider: Provider;
  score: number;
  remaining_capacity: number;
};

export async function getCandidates(clientId: string, limit = 5): Promise<Candidate[]> {
  const res = await fetch(
    `${API_URL}/api/v1/clients/${clientId}/candidates?limit=${limit}`,
  );
  if (!res.ok) {
    const detail = await res.text();
    throw new Error(`Failed to fetch candidates (${res.status}): ${detail}`);
  }
  return res.json();
}

export type SimulationRun = {
  id: string;
  name: string;
  scenario: Scenario;
  seed: number;
  provider_count: number;
  client_count: number;
  created_at: string;
};

export async function listSimulationRuns(): Promise<SimulationRun[]> {
  const res = await fetch(`${API_URL}/api/v1/simulation-runs`, { cache: "no-store" });
  if (!res.ok) throw new Error(`Failed to fetch simulation runs: ${res.status}`);
  return res.json();
}

export type SimulationRunCreate = {
  name: string;
  scenario?: Scenario;
  seed: number;
  provider_count: number;
  client_count: number;
};

export async function createSimulationRun(input: SimulationRunCreate): Promise<SimulationRun> {
  const res = await fetch(`${API_URL}/api/v1/simulation-runs`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input),
  });
  if (!res.ok) {
    const detail = await res.text();
    throw new Error(`Failed to create simulation run (${res.status}): ${detail}`);
  }
  return res.json();
}

export async function generateSimulationRun(runId: string): Promise<void> {
  const res = await fetch(`${API_URL}/api/v1/simulation-runs/${runId}/generate`, {
    method: "POST",
  });
  if (!res.ok) {
    const detail = await res.text();
    throw new Error(`Failed to generate population (${res.status}): ${detail}`);
  }
}
