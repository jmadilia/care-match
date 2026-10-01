import type { Candidate } from "@/lib/api";

export function CandidateList({ candidates }: { candidates: Candidate[] }) {
  if (candidates.length === 0) {
    return (
      <p className="text-sm" style={{ color: "var(--chart-text-secondary)" }}>
        No eligible provider in this pool has room right now, no provider licensed in that
        state and paneled with that insurer, or they are all at capacity.
      </p>
    );
  }

  return (
    <ul className="flex flex-col gap-3">
      {candidates.map((candidate, i) => (
        <li
          key={candidate.provider.id}
          className="flex items-start justify-between gap-4 rounded-md border p-3"
          style={{ borderColor: "var(--chart-gridline)" }}
        >
          <div>
            <p className="text-sm font-medium" style={{ color: "var(--chart-text-primary)" }}>
              {i + 1}. {candidate.provider.name}
            </p>
            <p className="mt-1 text-xs" style={{ color: "var(--chart-text-secondary)" }}>
              {candidate.provider.specialties.join(", ")} &middot;{" "}
              {candidate.provider.modalities.join(", ")} &middot;{" "}
              {candidate.provider.languages.join(", ")}
            </p>
          </div>
          <div className="shrink-0 text-right">
            <p
              className="text-sm font-semibold tabular-nums"
              style={{ color: "var(--chart-text-primary)" }}
            >
              {(candidate.score * 100).toFixed(0)}% fit
            </p>
            <p className="text-xs tabular-nums" style={{ color: "var(--chart-text-muted)" }}>
              {candidate.remaining_capacity} slot{candidate.remaining_capacity === 1 ? "" : "s"}{" "}
              open
            </p>
          </div>
        </li>
      ))}
    </ul>
  );
}
