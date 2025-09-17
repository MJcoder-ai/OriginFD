"use client";

import * as React from "react";
import { Badge } from "@originfd/ui";

import { ShipmentEvent } from "@/lib/epcis-client";
import { cn } from "@/lib/utils";

interface ShipmentTimelineProps {
  events: ShipmentEvent[];
}

const statusStyles: Record<ShipmentEvent["type"], string> = {
  pickup: "bg-blue-100 text-blue-800",
  loaded: "bg-purple-100 text-purple-800",
  arrived: "bg-yellow-100 text-yellow-800",
  delivered: "bg-green-100 text-green-800",
  exception: "bg-red-100 text-red-800",
};

export function ShipmentTimeline({ events }: ShipmentTimelineProps) {
  if (!events?.length) {
    return <p className="text-sm text-muted-foreground">No shipment events.</p>;
  }

  const sorted = [...events].sort(
    (a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime(),
  );
  const latest = sorted[sorted.length - 1];

  return (
    <ol className="relative ml-4 border-l pl-6">
      {sorted.map((event) => (
        <li key={`${event.type}-${event.timestamp}`} className="mb-6 ml-4">
          <div
            className={cn(
              "absolute -left-1.5 flex h-3 w-3 items-center justify-center rounded-full border border-background",
              event === latest ? "bg-blue-600" : "bg-muted",
            )}
          />
          <details>
            <summary className="flex cursor-pointer items-center gap-2">
              <Badge className={statusStyles[event.type]}>{event.type}</Badge>
              <span
                className={cn(
                  "text-sm",
                  event === latest && "font-semibold text-foreground",
                )}
              >
                {new Date(event.timestamp).toLocaleString()}
              </span>
              <span className="ml-auto text-xs text-muted-foreground">
                {event.sscc}
              </span>
            </summary>
            {event.sensors && event.sensors.length > 0 && (
              <div className="mt-2 space-y-1 text-sm text-muted-foreground">
                {event.sensors.map((s, idx) => (
                  <div key={idx}>
                    {s.type}: {s.value}
                    {s.unit && <span className="ml-1">{s.unit}</span>}
                  </div>
                ))}
              </div>
            )}
          </details>
        </li>
      ))}
    </ol>
  );
}

export default ShipmentTimeline;
