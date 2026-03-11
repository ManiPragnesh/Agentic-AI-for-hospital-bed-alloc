'use client';

import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { StatCard } from "@/components/StatCard";
import { Activity, Users } from "lucide-react";

export default function InsightsPage() {
  const [apiKey, setApiKey] = useState("");
  const [advice, setAdvice] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [metrics, setMetrics] = useState<any | null>(null);
  const [lastSavedAt, setLastSavedAt] = useState<string | null>(null);

  const loadMetrics = async () => {
    try {
      const res = await fetch(`/api/metrics`);
      const data = await res.json();
      setMetrics(data);
    } catch {
      // ignore rendering error state here; advisor can still work
    }
  };

  useEffect(() => {
    const savedAdvice = typeof window !== "undefined" ? localStorage.getItem("advisor:last") : null;
    const savedAt = typeof window !== "undefined" ? localStorage.getItem("advisor:last_at") : null;
    if (savedAdvice) setAdvice(savedAdvice);
    if (savedAt) setLastSavedAt(savedAt);
    loadMetrics();
  }, []);

  const fetchAdvice = async () => {
    setAdvice("");
    setError(null);
    setLoading(true);
    try {
      const res = await fetch(`/api/analyze/advisor`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ api_key: apiKey }),
      });
      if (!res.body) {
        throw new Error("Streaming not supported by the browser.");
      }
      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        const chunk = decoder.decode(value);
        setAdvice((prev) => prev + chunk);
      }
      const ts = new Date().toISOString();
      localStorage.setItem("advisor:last", advice);
      localStorage.setItem("advisor:last_at", ts);
      setLastSavedAt(ts);
      loadMetrics();
    } catch (e: any) {
      setError(e?.message || "Failed to stream advisor output");
    } finally {
      setLoading(false);
    }
  };

  const resetScenario = async (scenario: "NORMAL" | "FLU_SURGE" | "MASS_CASUALTY" | "STAFF_SHORTAGE") => {
    setError(null);
    try {
      await fetch(`/api/simulation/reset`, {
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
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-slate-900 dark:text-white">
            Insights
          </h1>
          <p className="mt-2 text-slate-600 dark:text-slate-300">
            This page is prepared for analytical insights and advisor outputs.
          </p>
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

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <Card className="lg:col-span-2">
            <CardHeader>
              <CardTitle>Advisor Strategy (Live)</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-end gap-3 mb-4">
                <div className="flex-1">
                  <label className="block text-sm text-slate-600 dark:text-slate-400 mb-1">
                    OpenAI API Key
                  </label>
                  <input
                    type="password"
                    placeholder="sk-..."
                    value={apiKey}
                    onChange={(e) => setApiKey(e.target.value)}
                    className="w-full rounded-md border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-slate-400"
                  />
                </div>
                <Button onClick={fetchAdvice} disabled={loading || !apiKey}>
                  {loading ? "Streaming..." : "Get Advice"}
                </Button>
              </div>
              {error && (
                <div className="mb-3 text-sm text-red-600">
                  {error}
                </div>
              )}
              <div className="min-h-[160px] rounded-lg border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-900 p-4 text-sm whitespace-pre-wrap">
                {advice || "Advisor output will appear here..."}
              </div>
              {lastSavedAt && (
                <div className="mt-2 text-xs text-slate-500">
                  Last saved: {new Date(lastSavedAt).toLocaleString()}
                </div>
              )}
              <p className="mt-2 text-xs text-slate-500">
                Placeholder content. Add widgets and strategy panels here later.
              </p>
            </CardContent>
          </Card>

          <div className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Operational KPIs</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-slate-600 dark:text-slate-400">
                  Placeholder widget for queue lengths, occupancy, and HSI.
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Upcoming Actions</CardTitle>
              </CardHeader>
              <CardContent>
                <ul className="list-disc pl-5 text-sm text-slate-600 dark:text-slate-400">
                  <li>Staffing optimization suggestions</li>
                  <li>Discharge prioritization candidates</li>
                  <li>Scenario planning shortcuts</li>
                </ul>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Scenarios</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex flex-wrap gap-2">
                  <Button variant="secondary" onClick={() => resetScenario("NORMAL")}>Normal</Button>
                  <Button variant="secondary" onClick={() => resetScenario("FLU_SURGE")}>Flu Surge</Button>
                  <Button variant="secondary" onClick={() => resetScenario("MASS_CASUALTY")}>Mass Casualty</Button>
                  <Button variant="secondary" onClick={() => resetScenario("STAFF_SHORTAGE")}>Staff Shortage</Button>
                </div>
                <div className="mt-3">
                  <Button size="sm" variant="outline" onClick={loadMetrics}>Refresh KPIs</Button>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
}
