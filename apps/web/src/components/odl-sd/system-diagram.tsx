"use client";

import * as React from "react";
import { Button, Card, CardContent, CardHeader, CardTitle } from "@originfd/ui";
import { Sun, Battery, Zap, Power, Grid3x3 } from "lucide-react";
import { ComponentInstance, Connection } from "@/lib/types";

interface PortMeta {
  id: string;
  side?: "left" | "right" | "top" | "bottom";
}

interface SystemDiagramProps {
  instances: ComponentInstance[];
  connections: Connection[];
  className?: string;
}

interface ComponentPosition {
  id: string;
  x: number;
  y: number;
  type: string;
}

type Layer =
  | "Electrical"
  | "Mechanical"
  | "Physical"
  | "Compliance"
  | "Finance"
  | "ESG";

interface ConnectionWithLayer extends Connection {
  layer?: Layer;
  from_port?: string;
  to_port?: string;
  from_component?: string;
  to_component?: string;
}

export function SystemDiagram({
  instances,
  connections,
  className,
}: SystemDiagramProps) {
  const svgRef = React.useRef<SVGSVGElement>(null);
  const [positions, setPositions] = React.useState<ComponentPosition[]>([]);
  const [layers, setLayers] = React.useState<Record<Layer, boolean>>({
    Electrical: true,
    Mechanical: true,
    Physical: true,
    Compliance: true,
    Finance: true,
    ESG: true,
  });
  const [ghostWire, setGhostWire] = React.useState<{
    x1: number;
    y1: number;
    x2: number;
    y2: number;
  } | null>(null);

  // Calculate component positions based on type and connections
  React.useEffect(() => {
    const newPositions: ComponentPosition[] = [];
    const width = 600;
    const height = 400;
    const margin = 60;

    // Group components by type for better layout
    const componentsByType: Record<string, ComponentInstance[]> = {};
    instances.forEach((component) => {
      if (!componentsByType[component.type]) {
        componentsByType[component.type] = [];
      }
      componentsByType[component.type].push(component);
    });

    // Define layout columns for different component types
    const typeLayout: Record<string, { column: number; priority: number }> = {
      pv_array: { column: 0, priority: 0 },
      battery: { column: 0, priority: 1 },
      inverter: { column: 1, priority: 0 },
      power_conversion_system: { column: 1, priority: 1 },
      grid_connection: { column: 2, priority: 0 },
      load: { column: 2, priority: 1 },
    };

    // Calculate positions
    let yOffset = margin;
    Object.entries(componentsByType).forEach(([type, components]) => {
      const layout = typeLayout[type] || { column: 1, priority: 0 };
      const x = margin + (layout.column * (width - 2 * margin)) / 2;

      components.forEach((component, index) => {
        newPositions.push({
          id: component.id,
          x: x + (index % 2) * 120 - 60, // Slight offset for multiple components of same type
          y: yOffset + Math.floor(index / 2) * 100,
          type: component.type,
        });
      });

      yOffset += Math.ceil(components.length / 2) * 100 + 60;
    });

    setPositions(newPositions);
  }, [instances]);

  const toggleLayer = (layer: Layer) =>
    setLayers((prev) => ({ ...prev, [layer]: !prev[layer] }));

  const isLayerVisible = (layer: Layer | undefined) => {
    if (!layer) return true;
    return layers[layer];
  };

  const handleMouseMove = (e: React.MouseEvent<SVGSVGElement, MouseEvent>) => {
    if (ghostWire && svgRef.current) {
      const rect = svgRef.current.getBoundingClientRect();
      setGhostWire({
        ...ghostWire,
        x2: e.clientX - rect.left,
        y2: e.clientY - rect.top,
      });
    }
  };

  const handlePortEnter = (x: number, y: number) => {
    setGhostWire({ x1: x, y1: y, x2: x, y2: y });
  };

  const handlePortLeave = () => setGhostWire(null);

  const exportSvg = () => {
    if (!svgRef.current) return;
    const serializer = new XMLSerializer();
    const source = serializer.serializeToString(svgRef.current);
    const blob = new Blob([source], { type: "image/svg+xml;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = "system-diagram.svg";
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  const getComponentIcon = (type: string) => {
    switch (type) {
      case "pv_array":
        return Sun;
      case "inverter":
        return Power;
      case "battery":
        return Battery;
      case "power_conversion_system":
        return Zap;
      default:
        return Grid3x3;
    }
  };

  const getComponentColor = (type: string) => {
    switch (type) {
      case "pv_array":
        return "text-yellow-600 bg-yellow-50 border-yellow-200";
      case "inverter":
        return "text-blue-600 bg-blue-50 border-blue-200";
      case "battery":
        return "text-green-600 bg-green-50 border-green-200";
      case "power_conversion_system":
        return "text-purple-600 bg-purple-50 border-purple-200";
      default:
        return "text-gray-600 bg-gray-50 border-gray-200";
    }
  };

  const getConnectionColor = (type: string) => {
    switch (type) {
      case "dc_electrical":
        return "stroke-blue-500";
      case "ac_electrical":
        return "stroke-green-500";
      case "communication":
        return "stroke-purple-500";
      default:
        return "stroke-gray-400";
    }
  };

  const getPositionById = (id: string) => {
    return positions.find((p) => p.id === id);
  };

  const getComponentName = (id: string) => {
    const component = instances.find((c) => c.id === id);
    return (
      component?.type
        .replace("_", " ")
        .replace(/\b\w/g, (l) => l.toUpperCase()) || id
    );
  };

  const getCapacityFromComponent = (id: string): string => {
    const component = instances.find((c) => c.id === id);
    if (!component) return "";

    const capacity =
      component.parameters.capacity_kw || component.parameters.power_kw;
    if (capacity) {
      if (capacity >= 1000) {
        return `${(capacity / 1000).toFixed(1)} MW`;
      }
      return `${capacity.toFixed(0)} kW`;
    }
    return "";
  };

  return (
    <Card className={className}>
      <CardHeader className="flex items-center justify-between">
        <CardTitle className="flex items-center gap-2">
          <Grid3x3 className="h-5 w-5" />
          System Architecture
        </CardTitle>
        <Button variant="outline" size="sm" onClick={exportSvg}>
          Export SLD
        </Button>
      </CardHeader>
      <CardContent>
        <div className="mb-4 flex flex-wrap gap-4 text-xs">
          {Object.entries(layers).map(([layer, visible]) => (
            <label key={layer} className="flex items-center gap-1">
              <input
                type="checkbox"
                checked={visible}
                onChange={() => toggleLayer(layer as Layer)}
              />
              {layer}
            </label>
          ))}
        </div>
        <div className="relative">
          <svg
            ref={svgRef}
            width="100%"
            height="400"
            viewBox="0 0 600 400"
            className="border rounded-lg bg-gray-50"
            onMouseMove={handleMouseMove}
          >
            {/* Draw ghost wire */}
            {ghostWire && (
              <line
                x1={ghostWire.x1}
                y1={ghostWire.y1}
                x2={ghostWire.x2}
                y2={ghostWire.y2}
                className="stroke-gray-400 stroke-1 stroke-dasharray-4 pointer-events-none"
              />
            )}

            {/* Draw connections */}
            {(connections as ConnectionWithLayer[])
              .filter((conn) => isLayerVisible(conn.layer))
              .map((connection) => {
                const fromPos = getPositionById(connection.from_component);
                const toPos = getPositionById(connection.to_component);

                if (!fromPos || !toPos) return null;

                return (
                  <g key={connection.id}>
                    {/* Connection line */}
                    <line
                      x1={fromPos.x}
                      y1={fromPos.y}
                      x2={toPos.x}
                      y2={toPos.y}
                      className={`${getConnectionColor(connection.connection_type)} stroke-2`}
                      markerEnd="url(#arrowhead)"
                    />

                    {/* Connection label */}
                    <text
                      x={(fromPos.x + toPos.x) / 2}
                      y={(fromPos.y + toPos.y) / 2 - 5}
                      textAnchor="middle"
                      className="text-xs fill-gray-600 bg-white"
                    >
                      <tspan className="bg-white px-1">
                        {connection.connection_type
                          .replace("_", " ")
                          .toUpperCase()}
                      </tspan>
                    </text>
                  </g>
                );
              })}

            {/* Arrow marker definition */}
            <defs>
              <marker
                id="arrowhead"
                markerWidth="10"
                markerHeight="7"
                refX="9"
                refY="3.5"
                orient="auto"
              >
                <polygon points="0 0, 10 3.5, 0 7" className="fill-gray-500" />
              </marker>
            </defs>

            {/* Draw components */}
            {positions.map((pos) => {
              const Icon = getComponentIcon(pos.type);
              const capacity = getCapacityFromComponent(pos.id);
              const instance = instances.find((i) => i.id === pos.id);
              const ports: PortMeta[] =
                (instance as any)?.metadata?.ports || [];

              const renderPorts = ports.map((port, i) => {
                const side = port.side || (i % 2 === 0 ? "left" : "right");
                const portsPerSide = Math.ceil(ports.length / 2);
                const indexOnSide = i % portsPerSide;
                const y =
                  pos.y - 30 + ((indexOnSide + 1) * 60) / (portsPerSide + 1);
                const x = side === "left" ? pos.x - 40 : pos.x + 40;
                return (
                  <circle
                    key={port.id}
                    cx={x}
                    cy={y}
                    r={4}
                    className="fill-white stroke-gray-500"
                    data-port-id={port.id}
                    onMouseEnter={() => handlePortEnter(x, y)}
                    onMouseLeave={handlePortLeave}
                  >
                    <title>{port.id}</title>
                  </circle>
                );
              });

              return (
                <g key={pos.id}>
                  {/* Component background */}
                  <rect
                    x={pos.x - 40}
                    y={pos.y - 30}
                    width="80"
                    height="60"
                    rx="8"
                    className={`${getComponentColor(pos.type)} border-2`}
                  />

                  {/* Ports */}
                  {renderPorts}

                  {/* Component icon */}
                  <foreignObject
                    x={pos.x - 12}
                    y={pos.y - 25}
                    width="24"
                    height="24"
                  >
                    <Icon className="h-6 w-6" />
                  </foreignObject>

                  {/* Component label */}
                  <text
                    x={pos.x}
                    y={pos.y + 5}
                    textAnchor="middle"
                    className="text-xs font-medium fill-gray-800"
                  >
                    {pos.id}
                  </text>

                  {/* Capacity label */}
                  {capacity && (
                    <text
                      x={pos.x}
                      y={pos.y + 18}
                      textAnchor="middle"
                      className="text-xs fill-gray-600"
                    >
                      {capacity}
                    </text>
                  )}
                </g>
              );
            })}
          </svg>

          {/* Legend */}
          <div className="mt-4 flex flex-wrap gap-4 text-sm">
            <div className="flex items-center gap-2">
              <div className="w-4 h-1 bg-blue-500"></div>
              <span>DC Electrical</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-4 h-1 bg-green-500"></div>
              <span>AC Electrical</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-4 h-1 bg-purple-500"></div>
              <span>Communication</span>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
