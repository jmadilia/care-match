"use client";

import type { StrategyAggregate, UrgencyTier } from "@/lib/api";
import { ChartTooltip } from "./ChartTooltip";
import { STRATEGY_ORDER, URGENCY_ORDER, strategyColorVar, strategyLabel } from "./strategies";
import { useBarTooltip } from "./useBarTooltip";

const CHART_HEIGHT = 200;
const GRIDLINES = [0, 25, 50, 75, 100];
const TIER_LABELS: Record<UrgencyTier, string> = {
  ROUTINE: "Routine",
  ELEVATED: "Elevated",
  URGENT: "Urgent",
};

// 12 bars (3 tiers x 4 strategies): too dense for a value on every bar, so
// values live in the tooltip and the results table, not as direct labels.
export function UrgencyChart({ aggregates }: { aggregates: StrategyAggregate[] }) {
  const { containerRef, tooltip, show, hide } = useBarTooltip();
  const byStrategy = new Map(aggregates.map((a) => [a.strategy, a]));

  return (
    <div>
      <h3 className="mb-3 text-sm font-medium" style={{ color: "var(--chart-text-primary)" }}>
        Fill rate by urgency tier
      </h3>
      <div ref={containerRef} className="relative">
        <div
          className="relative flex items-end justify-around gap-8 border-b px-4"
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
          {URGENCY_ORDER.map((tier) => (
            <div key={tier} className="relative z-[1] flex h-full flex-1 items-end justify-center gap-1.5">
              {STRATEGY_ORDER.map((strategy) => {
                const aggregate = byStrategy.get(strategy);
                const rate = aggregate?.mean_fill_rate_by_urgency[tier];
                if (rate === undefined) return null;
                const pct = rate * 100;
                const label = strategyLabel(strategy);
                return (
                  <div
                    key={strategy}
                    tabIndex={0}
                    role="img"
                    aria-label={`${label}, ${TIER_LABELS[tier]}: ${pct.toFixed(1)} percent fill rate`}
                    className="w-5 max-w-5 rounded-t-sm outline-none focus-visible:ring-2 focus-visible:ring-offset-2"
                    style={{ height: `${pct}%`, background: strategyColorVar(strategy) }}
                    onPointerEnter={(e) =>
                      show(e, `${TIER_LABELS[tier]} · ${label}`, [
                        {
                          label: "Fill rate",
                          value: `${pct.toFixed(1)}%`,
                          colorVar: strategyColorVar(strategy),
                        },
                      ])
                    }
                    onFocus={(e) =>
                      show(e, `${TIER_LABELS[tier]} · ${label}`, [
                        {
                          label: "Fill rate",
                          value: `${pct.toFixed(1)}%`,
                          colorVar: strategyColorVar(strategy),
                        },
                      ])
                    }
                    onPointerLeave={hide}
                    onBlur={hide}
                  />
                );
              })}
            </div>
          ))}
        </div>
        <div className="mt-2 flex justify-around gap-8 px-4">
          {URGENCY_ORDER.map((tier) => (
            <span
              key={tier}
              className="flex-1 text-center text-xs"
              style={{ color: "var(--chart-text-secondary)" }}
            >
              {TIER_LABELS[tier]}
            </span>
          ))}
        </div>
        <ChartTooltip data={tooltip} />
      </div>
    </div>
  );
}
