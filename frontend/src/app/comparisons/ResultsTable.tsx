import type { StrategyAggregate } from "@/lib/api";
import { STRATEGY_ORDER, strategyColorVar, strategyLabel } from "./strategies";

// Every value the charts show on hover lives here too, reachable without
// hovering anything, and it carries the two metrics the charts don't plot.
export function ResultsTable({ aggregates }: { aggregates: StrategyAggregate[] }) {
  const byStrategy = new Map(aggregates.map((a) => [a.strategy, a]));
  const rows = STRATEGY_ORDER.map((s) => byStrategy.get(s)).filter(
    (a): a is StrategyAggregate => a !== undefined,
  );

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-left text-sm">
        <thead>
          <tr style={{ color: "var(--chart-text-secondary)" }}>
            <th className="pb-2 pr-4 font-medium">Strategy</th>
            <th className="pb-2 pr-4 font-medium">Fill rate</th>
            <th className="pb-2 pr-4 font-medium">Match score</th>
            <th className="pb-2 font-medium">Utilization stdev</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((a) => (
            <tr
              key={a.strategy}
              className="border-t"
              style={{ borderColor: "var(--chart-gridline)" }}
            >
              <td className="py-2 pr-4">
                <span className="flex items-center gap-2" style={{ color: "var(--chart-text-primary)" }}>
                  <span
                    aria-hidden
                    className="inline-block h-2.5 w-2.5 rounded-full"
                    style={{ background: strategyColorVar(a.strategy) }}
                  />
                  {strategyLabel(a.strategy)}
                </span>
              </td>
              <td className="py-2 pr-4 tabular-nums" style={{ color: "var(--chart-text-primary)" }}>
                {(a.mean_fill_rate * 100).toFixed(1)}%{" "}
                <span style={{ color: "var(--chart-text-muted)" }}>
                  (±{(a.std_fill_rate * 100).toFixed(1)})
                </span>
              </td>
              <td className="py-2 pr-4 tabular-nums" style={{ color: "var(--chart-text-primary)" }}>
                {a.mean_match_score_mean.toFixed(3)}{" "}
                <span style={{ color: "var(--chart-text-muted)" }}>
                  (±{a.mean_match_score_std.toFixed(3)})
                </span>
              </td>
              <td className="py-2 tabular-nums" style={{ color: "var(--chart-text-primary)" }}>
                {a.mean_provider_utilization_std.toFixed(3)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
