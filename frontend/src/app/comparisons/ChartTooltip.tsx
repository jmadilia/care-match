import type { TooltipData } from "./useBarTooltip";

// Tooltips enhance, they never gate: every value shown here is also in the
// results table below, reachable without hovering anything.
export function ChartTooltip({ data }: { data: TooltipData | null }) {
  if (!data) return null;

  return (
    <div
      className="pointer-events-none absolute z-10 min-w-40 -translate-x-1/2 -translate-y-full rounded-md px-3 py-2 text-xs shadow-md"
      style={{
        left: data.x,
        top: data.y - 8,
        background: "var(--chart-surface)",
        border: "1px solid var(--chart-gridline)",
      }}
    >
      <div className="mb-1 font-medium" style={{ color: "var(--chart-text-primary)" }}>
        {data.title}
      </div>
      {data.rows.map((row) => (
        <div key={row.label} className="flex items-center gap-1.5 py-0.5">
          {row.colorVar && (
            <span
              aria-hidden
              className="inline-block h-0.5 w-3 shrink-0 rounded-full"
              style={{ background: row.colorVar }}
            />
          )}
          <span style={{ color: "var(--chart-text-secondary)" }}>{row.label}</span>
          <span
            className="ml-auto font-semibold tabular-nums"
            style={{ color: "var(--chart-text-primary)" }}
          >
            {row.value}
          </span>
        </div>
      ))}
    </div>
  );
}
