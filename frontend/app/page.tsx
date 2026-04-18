'use client';

import { useEffect, useState } from 'react';
// import { AdvisorPanel } from '@/components/AdvisorPanel'; // Removed
import { StatCard } from '@/components/StatCard';
import { HospitalMap } from '@/components/HospitalMap';
import { Users, DollarSign, Activity, Clock } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { LiveChart } from '@/components/LiveChart';
import Link from 'next/link';

// Types
interface Metrics {
  time: number;
  financials: { revenue: number; cost: number; profit: number };
  departments: Record<string, any>;
  staff_status: { assigned: number; total: number; ratio: number; is_safe: boolean };
  recent_logs?: Array<{ Time: number; Event: string }>; // Added for recent events log
}

interface ChartPoint {
  time: number;
  generalQueue: number;
  icuQueue: number;
  emerQueue: number;
}

export default function Dashboard() {
  const [metrics, setMetrics] = useState<Metrics | null>(null);
  const [history, setHistory] = useState<ChartPoint[]>([]);
  const [isRunning, setIsRunning] = useState(false);
  const API_BASE = "http://127.0.0.1:8000";

  const fetchMetrics = async () => {
    try {
      const res = await fetch(`http://127.0.0.1:8000/api/metrics`);
      const data = await res.json();
      setMetrics(data);

      // Update History Buffer
      setHistory(prev => {
        const newPoint = {
          time: data.time,
          generalQueue: data.departments['General'].queue_length,
          icuQueue: data.departments['ICU'].queue_length,
          emerQueue: data.departments['Emergency'].queue_length
        };
        const newBody = [...prev, newPoint];
        if (newBody.length > 30) newBody.shift(); // Keep last 30
        return newBody;
      });

    } catch (e) {
      console.error("Failed to fetch metrics", e);
    }
  };

  const stepSim = async () => {
    await fetch(`http://127.0.0.1:8000/api/simulation/step`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ hours: 1 })
    });
    fetchMetrics();
  };

  const resetSim = async () => {
    await fetch(`http://127.0.0.1:8000/api/simulation/reset`, { method: 'POST' });
    fetchMetrics();
    setHistory([]);
  }

  // Polling loop if running
  useEffect(() => {
    let interval: NodeJS.Timeout;
    if (isRunning) {
      interval = setInterval(stepSim, 2000); // Step every 2s
    }
    return () => clearInterval(interval);
  }, [isRunning]);

  // Initial Fetch
  useEffect(() => { fetchMetrics(); }, []);

  if (!metrics) return <div className="flex h-screen items-center justify-center">Connecting to Simulation...</div>;

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-black p-8 font-sans">

      {/* Header */}
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-slate-900 dark:text-white">Hospital AI Dashboard <span className="text-xs text-slate-400">v1.2-Direct</span></h1>
        </div>
        <div className="flex gap-2">
          <Link href="/settings">
            <Button variant="outline">
              ⚙️ Settings
            </Button>
          </Link>
          <button
            onClick={resetSim}
            className="px-4 py-2 bg-slate-200 hover:bg-slate-300 rounded-lg font-medium transition-colors"
          >
            Reset
          </button>
          <button
            onClick={() => setIsRunning(!isRunning)}
            className={`px-4 py-2 rounded-lg font-medium text-white transition-colors ${isRunning ? 'bg-red-500 hover:bg-red-600' : 'bg-green-500 hover:bg-green-600'}`}
          >
            {isRunning ? 'Pause Sim' : 'Start Sim'}
          </button>
          <button
            onClick={stepSim}
            className="px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded-lg font-medium transition-colors"
          >
            Step +1h
          </button>
        </div>
      </div>

      {/* Top Section: KPIs & Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6 mb-8">

        {/* Metrics Grid (Full Width) */}
        <StatCard
          title="Time Elapsed"
          value={`${metrics.time}h`}
          icon={<Clock className="text-blue-500" />}
          subtext="Simulation Hours"
        />

        <StatCard
          title="Staff Strain"
          value={metrics.staff_status.ratio.toFixed(1)}
          icon={<Users className="text-purple-500" />}
          color={metrics.staff_status.is_safe ? "text-green-500" : "text-red-500"}
          subtext={metrics.staff_status.is_safe ? "Safe Load" : "CRITICAL LOAD"}
        />
        <StatCard
          title="Total Patients"
          value={
            Object.values(metrics.departments).reduce((acc: number, d: any) => acc + d.queue_length + d.occupancy, 0)
          }
          icon={<Activity className="text-orange-500" />}
          subtext="Active in System"
        />
      </div>

      {/* Charts Section */}
      <div className="mb-8">
        <Card className="p-6">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-xl font-semibold">Queue Trends</h2>
          </div>
          <LiveChart data={history} />
        </Card>
      </div>

      {/* Main Content Grid: Floor Plan & Logs */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">

        {/* Left: Floor Plan covering 2/3 */}
        <div className="lg:col-span-2 space-y-6">
          <Card className="border-none shadow-none bg-transparent">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-xl font-semibold">Live Floor Plan</h2>
              <span className="text-xs bg-green-100 text-green-800 px-2 py-1 rounded-full">Live Updates</span>
            </div>
            <HospitalMap data={metrics} />
          </Card>
        </div>

        {/* Right: Recent Events */}
        <div className="space-y-6">
          <Card className="p-4 h-full">
            <h3 className="font-semibold mb-3">Recent Activity</h3>
            <div className="space-y-2 max-h-[500px] overflow-y-auto text-sm">
              {metrics.recent_logs?.map((log: any, i: number) => (
                <div key={i} className="flex justify-between border-b border-slate-100 pb-2 last:border-0">
                  <span className="text-slate-500 text-xs">{log.Time}h</span>
                  <span className="truncate ml-2">{log.Event}</span>
                </div>
              ))}
            </div>
          </Card>
        </div>

      </div>
    </div>
  );
}
