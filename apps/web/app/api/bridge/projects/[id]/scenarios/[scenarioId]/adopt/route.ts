import { NextRequest, NextResponse } from "next/server";
import { findProject } from "../../../../../shared-data";
import path from "path";
import { promises as fs } from "fs";

export async function POST(
  request: NextRequest,
  { params }: { params: { id: string; scenarioId: string } },
) {
  const { id, scenarioId } = params;
  const project = findProject(id);
  if (project) {
    (project as any).adopted_scenario = scenarioId;
    (project as any).updated_at = new Date().toISOString();
  }

  // lookup scenario data to store audit
  const filePath = path.join(
    process.cwd(),
    "services",
    "orchestrator",
    "planner",
    "mock_scenarios.json",
  );
  const raw = await fs.readFile(filePath, "utf-8");
  const scenarios = JSON.parse(raw);
  const scenario = scenarios.find((s: any) => s.id === scenarioId);

  if (scenario) {
    const auditPayload = {
      project_id: id,
      name: scenario.name,
      irr_percent: scenario.irr_percent,
      lcoe_per_kwh: scenario.lcoe_per_kwh,
      npv_usd: scenario.npv_usd,
    };
    try {
      const apiBaseUrl =
        process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      await fetch(`${apiBaseUrl}/scenarios`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(auditPayload),
      });
    } catch (e) {
      console.warn("Failed to store scenario audit", e);
    }
  }

  // trigger notification
  const origin = new URL(request.url).origin;
  await fetch(`${origin}/api/notifications`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      projectId: id,
      scenarioId,
      message: `Scenario ${scenarioId} adopted`,
    }),
  });

  return NextResponse.json({ status: "adopted", project });
}
