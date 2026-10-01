import { STRATEGY_ORDER, strategyColorVar, strategyLabel } from "./strategies";

// A single shared legend for both charts below: they use the same color
// mapping, so one legend is the dependable identity channel for both
// instead of repeating (or worse, redefining) it per chart.
export function StrategyLegend() {
  return (
    <div className="flex flex-wrap gap-4 text-sm" style={{ color: "var(--chart-text-secondary)" }}>
      {STRATEGY_ORDER.map((strategy) => (
        <div key={strategy} className="flex items-center gap-2">
          <span
            aria-hidden
            className="inline-block h-2.5 w-2.5 rounded-full"
            style={{ background: strategyColorVar(strategy) }}
          />
          <span>{strategyLabel(strategy)}</span>
        </div>
      ))}
    </div>
  );
}
