// Fixed display order and identity for the four strategies. Never derived from
// whatever order the API happens to return, so color/position stay stable
// across requests and a filtered view never repaints the survivors.
export const STRATEGY_ORDER = [
  "greedy",
  "stable_matching",
  "optimal",
  "waitlist_priority",
] as const;

export type StrategyKey = (typeof STRATEGY_ORDER)[number];

export const STRATEGY_LABELS: Record<StrategyKey, string> = {
  greedy: "Greedy",
  stable_matching: "Stable matching",
  optimal: "Optimal",
  waitlist_priority: "Waitlist priority",
};

// References the CSS custom properties defined in globals.css, which swap
// value under prefers-color-scheme, so these resolve correctly in both modes.
export const STRATEGY_COLOR_VAR: Record<StrategyKey, string> = {
  greedy: "var(--series-greedy)",
  stable_matching: "var(--series-stable-matching)",
  optimal: "var(--series-optimal)",
  waitlist_priority: "var(--series-waitlist-priority)",
};

export function strategyLabel(strategy: string): string {
  return STRATEGY_LABELS[strategy as StrategyKey] ?? strategy;
}

export function strategyColorVar(strategy: string): string {
  return STRATEGY_COLOR_VAR[strategy as StrategyKey] ?? "var(--chart-text-muted)";
}

export const URGENCY_ORDER = ["ROUTINE", "ELEVATED", "URGENT"] as const;
