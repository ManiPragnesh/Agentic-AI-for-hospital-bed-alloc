'use client';

import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { StatCard } from "@/components/StatCard";
import { Activity, Users } from "lucide-react";
import { AdvisorPanel } from "@/components/AdvisorPanel";

export default function InsightsPage() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [metrics, setMetrics] = useState<any | null>(null);

  const loadMetrics = async () => {
    try {
      const res = await fetch(`http://127.0.0.1:8000/api/metrics`);
      const data = await res.json();
      setMetrics(data);
    } catch {
      // ignore rendering error
    }
  };

  useEffect(() => {
    loadMetrics();
  }, []);

  const resetScenario = async (scenario: "NORMAL" | "FLU_SURGE" | "MASS_CASUALTY" | "STAFF_SHORTAGE") => {
    setError(null);
    try {
      await fetch(`http://127.0.0.1:8000/api/simulation/reset`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ scenario }),
      });
      await loadMetrics();
    } catch (e: any) {
      setError(e?.message || "Failed to reset scenario");
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-black p-8">
      <div className="max-w-6xl mx-auto space-y-8">
        <div className="flex justify-between items-end">
          <div>
            <h1 className="text-3xl font-bold tracking-tight text-slate-900 dark:text-white">
              Agentic Insights
            </h1>
            <p className="mt-2 text-slate-600 dark:text-slate-300">
              Real-time resource optimization strategies and local AI analysis.
            </p>
          </div>
          <div className="text-xs bg-slate-200 dark:bg-slate-800 px-3 py-1.5 rounded-lg font-mono text-slate-500">
            OFFLINE MODE ENABLED
          </div>
        </div>

        {/* KPI Row */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <StatCard
            title="Hospital Stability Index"
            value={metrics?.global?.hsi ?? "--"}
            icon={<Activity className="text-green-500" />}
            subtext="Higher is better"
          />
          <StatCard
            title="Staff Ratio"
            value={metrics?.staff_status?.ratio?.toFixed?.(1) ?? "--"}
            icon={<Users className="text-purple-500" />}
            color={metrics?.staff_status?.is_safe ? "text-green-500" : "text-red-500"}
            subtext={metrics?.staff_status?.is_safe ? "Safe Load" : "CRITICAL LOAD"}
          />
          <StatCard
            title="Total Patients"
            value={
              metrics
                ? Object.values(metrics.departments || {}).reduce((acc: number, d: any) => acc + d.queue_length + d.occupancy, 0)
                : "--"
            }
            icon={<Activity className="text-orange-500" />}
            subtext="Active in System"
          />
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Main Insights Area */}
          <div className="lg:col-span-2 space-y-6">
             <AdvisorPanel />
             
             <Card>
              <CardHeader>
                <CardTitle>Operational Health</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="p-4 bg-slate-100 dark:bg-slate-900 rounded-lg">
                    <p className="text-sm font-medium">Departmental Efficiency</p>
                    <p className="text-xs text-slate-500 mt-1">Analyzing cross-ward bed availability vs incoming Poisson arrival distribution.</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Sidebar / Scenarios */}
          <div className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="text-sm uppercase tracking-wider text-slate-500">Simulation Control</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-1 gap-2">
                  <Button variant="outline" className="justify-start" onClick={() => resetScenario("NORMAL")}>🟢 Normal State</Button>
                  <Button variant="outline" className="justify-start" onClick={() => resetScenario("FLU_SURGE")}>🟡 Flu Surge</Button>
                  <Button variant="outline" className="justify-start" onClick={() => resetScenario("MASS_CASUALTY")}>🟠 Mass Casualty</Button>
                  <Button variant="outline" className="justify-start" onClick={() => resetScenario("STAFF_SHORTAGE")}>🔴 Staff Shortage</Button>
                </div>
                <div className="pt-4 border-t border-slate-100 dark:border-slate-800">
                  <Button className="w-full" size="sm" variant="default" onClick={loadMetrics}>Sync Latest Metrics</Button>
                </div>
              </CardContent>
            </Card>

            <Card className="bg-indigo-50 dark:bg-indigo-950/20 border-indigo-100 dark:border-indigo-900">
              <CardHeader>
                <CardTitle className="text-sm text-indigo-600 dark:text-indigo-400">Agent Note</CardTitle>
              </CardHeader>
              <CardContent className="text-xs text-indigo-700 dark:text-indigo-300">
                PPO-based Reinforcement Learning is active in the background, managing admission priorities based on the learned reward function.
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
}
