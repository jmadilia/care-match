"use client";

import type { StrategyAggregate } from "@/lib/api";
import { ChartTooltip } from "./ChartTooltip";
import { STRATEGY_ORDER, strategyColorVar, strategyLabel } from "./strategies";
import { useBarTooltip } from "./useBarTooltip";

const CHART_HEIGHT = 200;
const GRIDLINES = [0, 25, 50, 75, 100];

export function FillRateChart({ aggregates }: { aggregates: StrategyAggregate[] }) {
  const { containerRef, tooltip, show, hide } = useBarTooltip();
  const byStrategy = new Map(aggregates.map((a) => [a.strategy, a]));
  const bars = STRATEGY_ORDER.map((s) => byStrategy.get(s)).filter(
    (a): a is StrategyAggregate => a !== undefined,
  );

  return (
    <div>
      <h3 className="mb-3 text-sm font-medium" style={{ color: "var(--chart-text-primary)" }}>
        Fill rate by strategy
      </h3>
      <div ref={containerRef} className="relative">
        <div
          className="relative flex items-end justify-around gap-6 border-b px-4"
          style={{ height: CHART_HEIGHT, borderColor: "var(--chart-baseline)" }}
        >
          {GRIDLINES.map((pct) => (
            <div
              key={pct}
              aria-hidden
              className="absolute inset-x-0 border-t"
              style={{ bottom: `${pct}%`, borderColor: "var(--chart-gridline)" }}
            />
          ))}
          {bars.map((aggregate) => {
            const pct = aggregate.mean_fill_rate * 100;
            const label = strategyLabel(aggregate.strategy);
            return (
              <div
                key={aggregate.strategy}
                className="relative z-[1] flex h-full flex-1 flex-col items-center justify-end gap-2"
              >
                <span
                  className="text-xs font-medium tabular-nums"
                  style={{ color: "var(--chart-text-primary)" }}
                >
                  {pct.toFixed(1)}%
                </span>
                <div
                  tabIndex={0}
                  role="img"
                  aria-label={`${label}: ${pct.toFixed(1)} percent fill rate, standard deviation ${(aggregate.std_fill_rate * 100).toFixed(1)} points`}
                  className="w-6 max-w-6 rounded-t-sm outline-none focus-visible:ring-2 focus-visible:ring-offset-2"
                  style={{ height: `${pct}%`, background: strategyColorVar(aggregate.strategy) }}
                  onPointerEnter={(e) =>
                    show(e, label, [
                      { label: "Fill rate", value: `${pct.toFixed(1)}%` },
                      {
                        label: "Std dev",
                        value: `${(aggregate.std_fill_rate * 100).toFixed(1)} pts`,
                      },
                    ])
                  }
                  onFocus={(e) =>
                    show(e, label, [
                      { label: "Fill rate", value: `${pct.toFixed(1)}%` },
                      {
                        label: "Std dev",
                        value: `${(aggregate.std_fill_rate * 100).toFixed(1)} pts`,
                      },
                    ])
                  }
                  onPointerLeave={hide}
                  onBlur={hide}
                />
              </div>
            );
          })}
        </div>
        <div className="mt-2 flex justify-around gap-6 px-4">
          {bars.map((aggregate) => (
            <span
              key={aggregate.strategy}
              className="flex-1 text-center text-xs"
              style={{ color: "var(--chart-text-secondary)" }}
            >
              {strategyLabel(aggregate.strategy)}
            </span>
          ))}
        </div>
        <ChartTooltip data={tooltip} />
      </div>
    </div>
  );
}
