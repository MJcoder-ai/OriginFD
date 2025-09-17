"use client";

import * as React from "react";
import { Button } from "@originfd/ui";

export type DocType = "sld" | "wiring" | "fault";

interface RedactionBox {
  x: number;
  y: number;
  width: number;
  height: number;
}

interface RedactionOverlayProps {
  src: string;
  type: "image" | "video";
  docType?: DocType;
}

export default function RedactionOverlay({
  src,
  type,
  docType = "sld",
}: RedactionOverlayProps) {
  const containerRef = React.useRef<HTMLDivElement>(null);
  const [redactions, setRedactions] = React.useState<RedactionBox[]>([]);
  const [drawing, setDrawing] = React.useState(false);
  const [start, setStart] = React.useState<{ x: number; y: number } | null>(
    null,
  );
  const [tempBox, setTempBox] = React.useState<RedactionBox | null>(null);

  const getRelativePos = (e: React.MouseEvent) => {
    const rect = containerRef.current!.getBoundingClientRect();
    return { x: e.clientX - rect.left, y: e.clientY - rect.top };
  };

  const handleMouseDown = (e: React.MouseEvent) => {
    if (!containerRef.current) return;
    const pos = getRelativePos(e);
    setStart(pos);
    setTempBox({ x: pos.x, y: pos.y, width: 0, height: 0 });
    setDrawing(true);
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    if (!drawing || !start) return;
    const pos = getRelativePos(e);
    setTempBox({
      x: Math.min(pos.x, start.x),
      y: Math.min(pos.y, start.y),
      width: Math.abs(pos.x - start.x),
      height: Math.abs(pos.y - start.y),
    });
  };

  const handleMouseUp = () => {
    if (drawing && tempBox) {
      setRedactions((prev) => [...prev, tempBox]);
    }
    setDrawing(false);
    setStart(null);
    setTempBox(null);
  };

  const saveRedactions = async () => {
    try {
      await fetch("/api/media/redaction", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          original_uri: src,
          redacted_uri: `${src}#redacted`,
          doc_type: docType,
          boxes: redactions,
        }),
      });
    } catch (err) {
      console.error("Failed to save redactions", err);
    }
  };

  return (
    <div className="space-y-2">
      {redactions.length > 0 && (
        <div
          data-testid="privacy-banner"
          className="bg-yellow-100 text-yellow-800 text-sm px-2 py-1 rounded"
        >
          Privacy: redactions applied
        </div>
      )}
      <div
        ref={containerRef}
        data-testid="redaction-overlay"
        className="relative inline-block border"
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
      >
        {type === "image" ? (
          <img
            src={src}
            alt="media"
            className="w-[400px] h-[300px] object-cover select-none pointer-events-none"
          />
        ) : (
          <video
            src={src}
            className="w-[400px] h-[300px] object-cover pointer-events-none"
          />
        )}
        {redactions.map((box, i) => (
          <div
            key={i}
            data-testid="redaction-box"
            style={{
              left: box.x,
              top: box.y,
              width: box.width,
              height: box.height,
            }}
            className="absolute bg-black/60 backdrop-blur-sm border border-white"
          />
        ))}
        {tempBox && (
          <div
            style={{
              left: tempBox.x,
              top: tempBox.y,
              width: tempBox.width,
              height: tempBox.height,
            }}
            className="absolute border border-dashed border-white bg-black/40"
          />
        )}
      </div>
      {redactions.length > 0 && (
        <Button onClick={saveRedactions}>Save Redactions</Button>
      )}
    </div>
  );
}
