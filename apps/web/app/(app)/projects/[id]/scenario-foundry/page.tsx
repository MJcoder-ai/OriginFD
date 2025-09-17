"use client";

import { useQuery } from "@tanstack/react-query";
import { useParams } from "next/navigation";
import { Card, CardContent, CardHeader, CardTitle, Button } from "@originfd/ui";
import { apiClient } from "@/lib/api-client";

interface Scenario {
  id: string;
  name: string;
  irr_percent: number;
  lcoe_per_kwh: number;
  npv_usd: number;
}

export default function ScenarioFoundryPage() {
  const params = useParams();
  const projectId = params.id as string;

  const { data: scenarios = [] } = useQuery<Scenario[]>({
    queryKey: ["scenarios", projectId],
    queryFn: () => apiClient.getProjectScenarios(projectId),
    enabled: !!projectId,
  });

  const adopt = async (scenarioId: string) => {
    await apiClient.adoptScenario(projectId, scenarioId);
  };

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Scenario Foundry</h1>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {scenarios.map((s) => (
          <Card key={s.id}>
            <CardHeader>
              <CardTitle>{s.name}</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              <div>IRR: {s.irr_percent}%</div>
              <div>LCOE: ${s.lcoe_per_kwh.toFixed(3)}/kWh</div>
              <div>NPV: ${s.npv_usd.toLocaleString()}</div>
              <Button className="mt-2" onClick={() => adopt(s.id)}>
                Adopt Scenario
              </Button>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
