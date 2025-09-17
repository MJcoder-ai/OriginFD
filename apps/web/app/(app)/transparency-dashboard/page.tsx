"use client";

import * as React from "react";
import { useQuery } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";
import { Card, CardHeader, CardTitle, CardContent } from "@originfd/ui";

export default function TransparencyDashboardPage() {
  const tenantId = "demo";

  const { data: psu } = useQuery({
    queryKey: ["psu-usage", tenantId],
    queryFn: () => apiClient.getPsuUsage(tenantId),
  });

  const { data: escrow } = useQuery({
    queryKey: ["escrow", tenantId],
    queryFn: () => apiClient.getEscrowStatus(tenantId),
  });

  const { data: tx } = useQuery({
    queryKey: ["transactions", tenantId],
    queryFn: () => apiClient.getTransactionHistory(tenantId),
  });

  const totalFees = React.useMemo(() => {
    return (
      tx?.transactions.reduce((sum: number, t: any) => sum + (t.fee || 0), 0) ||
      0
    );
  }, [tx]);

  const totalSavings = React.useMemo(() => {
    return (
      psu?.events.reduce((sum: number, e: any) => sum + (e.savings || 0), 0) ||
      0
    );
  }, [psu]);

  const totalCarbon = React.useMemo(() => {
    return (
      psu?.events.reduce((sum: number, e: any) => sum + (e.carbon || 0), 0) || 0
    );
  }, [psu]);

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold tracking-tight">
        Transparency Dashboard
      </h1>
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader>
            <CardTitle>PSU Consumption</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold">{psu?.total_psu ?? 0}</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Fees Accrued</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold">${totalFees.toFixed(2)}</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Savings</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold">${totalSavings.toFixed(2)}</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Carbon Impact</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold">{totalCarbon.toFixed(2)} tCO₂e</p>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
