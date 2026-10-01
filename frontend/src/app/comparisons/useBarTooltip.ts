"use client";

import { type RefObject, useRef, useState } from "react";

export type TooltipRow = { label: string; value: string; colorVar?: string };

export type TooltipData = {
  x: number;
  y: number;
  title: string;
  rows: TooltipRow[];
};

type BarEvent = { currentTarget: HTMLElement };

export function useBarTooltip(): {
  containerRef: RefObject<HTMLDivElement | null>;
  tooltip: TooltipData | null;
  show: (event: BarEvent, title: string, rows: TooltipRow[]) => void;
  hide: () => void;
} {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const [tooltip, setTooltip] = useState<TooltipData | null>(null);

  function show(event: BarEvent, title: string, rows: TooltipRow[]) {
    const container = containerRef.current;
    if (!container) return;
    const barRect = event.currentTarget.getBoundingClientRect();
    const containerRect = container.getBoundingClientRect();
    setTooltip({
      x: barRect.left - containerRect.left + barRect.width / 2,
      y: barRect.top - containerRect.top,
      title,
      rows,
    });
  }

  function hide() {
    setTooltip(null);
  }

  return { containerRef, tooltip, show, hide };
}
