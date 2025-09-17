"use client";
import * as React from "react";
import type { OdlDocument } from "@/lib/types";
import { useSelection, useCanvasBus } from "./bus";
import { Map, Grid3x3 } from "lucide-react";

export function SiteCanvas({
  projectId,
  document,
  activeLayers = ["equipment", "routes", "civil"],
}: {
  projectId: string;
  document?: OdlDocument;
  activeLayers?: string[];
}) {
  const { instanceId } = useSelection();
  const bus = useCanvasBus();
  // Minimal stub: render a couple of footprints based on libraries placement.location
  const libs = (document as any)?.libraries?.components || [];
  const items = libs.slice(0, 12);

  // Show welcome state if no components
  if (!items.length) {
    return (
      <div className="w-full h-full relative" data-canvas-root>
        <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
          <div className="pointer-events-auto">
            <div className="text-center">
              <div className="w-16 h-16 mx-auto mb-4 bg-secondary rounded-lg flex items-center justify-center">
                <Map className="w-8 h-8 text-primary" />
              </div>
              <h3 className="text-lg font-medium text-foreground mb-2">
                Canvas Ready
              </h3>
              <p className="text-sm text-muted-foreground mb-4 max-w-sm">
                Your site layout canvas is ready. Equipment and layout elements
                will appear here when you add them to your project.
              </p>
              <div className="flex items-center justify-center gap-2 text-xs text-muted-foreground">
                <span>Use</span>
                <kbd className="px-1.5 py-0.5 bg-muted border border-border rounded text-xs font-mono">
                  Components
                </kbd>
                <span>or</span>
                <kbd className="px-1.5 py-0.5 bg-muted border border-border rounded text-xs font-mono">
                  Models
                </kbd>
                <span>to get started</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="w-full h-full" data-canvas-root>
      <svg
        viewBox="0 0 800 480"
        className="w-full h-full rounded border bg-card"
      >
        <rect x={0} y={0} width={800} height={480} className="fill-card" />
        {activeLayers.includes("equipment") &&
          items.map((c: any, i: number) => {
            const x = 40 + (i % 6) * 120;
            const y = 40 + Math.floor(i / 6) * 160;
            const id = c.id ?? String(i);
            const selected =
              instanceId && (instanceId === id || instanceId === c.part_number);
            return (
              <g
                key={id}
                transform={`translate(${x},${y})`}
                onClick={() => bus.select(id)}
                className="cursor-pointer"
              >
                <rect
                  width="100"
                  height="80"
                  rx="8"
                  className={
                    selected
                      ? "fill-card stroke-2 stroke-foreground"
                      : "fill-muted stroke-border"
                  }
                />
                <text
                  x="50"
                  y="24"
                  textAnchor="middle"
                  className="text-[10px] fill-foreground"
                >
                  {c.category || "Equipment"}
                </text>
                {c.part_number && (
                  <text
                    x="50"
                    y="42"
                    textAnchor="middle"
                    className="text-[9px] fill-muted-foreground"
                  >
                    {c.part_number}
                  </text>
                )}
                {c.placement?.location && (
                  <text
                    x="50"
                    y="60"
                    textAnchor="middle"
                    className="text-[9px] fill-muted-foreground"
                  >
                    {c.placement.location}
                  </text>
                )}
              </g>
            );
          })}
      </svg>
    </div>
  );
}

export default SiteCanvas;
