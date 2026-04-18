'use client';

import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Download, FileText, TrendingUp } from "lucide-react";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar, Legend } from 'recharts';

// Mock historical data for the charts
const weeklyAdmissionsData = [
  { day: 'Mon', emergency: 12, icu: 3, general: 25 },
  { day: 'Tue', emergency: 15, icu: 4, general: 28 },
  { day: 'Wed', emergency: 10, icu: 2, general: 22 },
  { day: 'Thu', emergency: 18, icu: 5, general: 30 },
  { day: 'Fri', emergency: 22, icu: 6, general: 35 },
  { day: 'Sat', emergency: 25, icu: 7, general: 38 },
  { day: 'Sun', emergency: 20, icu: 5, general: 31 },
];

const waitTimeData = [
  { time: '08:00', wait: 15 },
  { time: '10:00', wait: 25 },
  { time: '12:00', wait: 45 },
  { time: '14:00', wait: 35 },
  { time: '16:00', wait: 55 },
  { time: '18:00', wait: 65 },
  { time: '20:00', wait: 40 },
];

export default function ReportsPage() {
  const [metrics, setMetrics] = useState<any | null>(null);

  useEffect(() => {
    // Fetch live metrics just to have some live data context if needed
    fetch('http://127.0.0.1:8000/api/metrics')
      .then(res => res.json())
      .then(data => setMetrics(data))
      .catch(err => console.error("Failed to fetch live metrics:", err));
  }, []);

  const handleDownload = () => {
    // Placeholder for actual PDF/CSV generation
    alert("Downloading generated summary report...");
  };

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-black p-8">
      <div className="max-w-6xl mx-auto space-y-8">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <h1 className="text-3xl font-bold tracking-tight text-slate-900 dark:text-white">
              Reports & Analytics
            </h1>
            <p className="mt-2 text-slate-600 dark:text-slate-300">
              Detailed historical performance, department charts, and downloadable summaries.
            </p>
          </div>
          <div className="flex gap-3">
            <Button variant="outline" className="flex items-center gap-2" onClick={handleDownload}>
              <FileText className="w-4 h-4" /> Export CSV
            </Button>
            <Button className="flex items-center gap-2" onClick={handleDownload}>
              <Download className="w-4 h-4" /> Download Full Report
            </Button>
          </div>
        </div>

        {/* Charts Row */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <Card>
            <CardHeader>
              <CardTitle>Weekly Admissions by Department</CardTitle>
              <CardDescription>Historical volume across Emergency, ICU, and General.</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="h-[300px] w-full mt-4">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={weeklyAdmissionsData}>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#E2E8F0" />
                    <XAxis dataKey="day" axisLine={false} tickLine={false} tick={{ fill: '#64748B', fontSize: 12 }} />
                    <YAxis axisLine={false} tickLine={false} tick={{ fill: '#64748B', fontSize: 12 }} />
                    <Tooltip 
                      contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }}
                      cursor={{ fill: 'rgba(241, 245, 249, 0.5)' }}
                    />
                    <Legend iconType="circle" wrapperStyle={{ paddingTop: '20px' }} />
                    <Bar dataKey="emergency" name="Emergency" stackId="a" fill="#F97316" radius={[0, 0, 4, 4]} />
                    <Bar dataKey="icu" name="ICU" stackId="a" fill="#EF4444" />
                    <Bar dataKey="general" name="General Ward" stackId="a" fill="#3B82F6" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Average Wait Times (Today)</CardTitle>
              <CardDescription>Triage queue wait time progression (minutes).</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="h-[300px] w-full mt-4">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={waitTimeData}>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#E2E8F0" />
                    <XAxis dataKey="time" axisLine={false} tickLine={false} tick={{ fill: '#64748B', fontSize: 12 }} />
                    <YAxis axisLine={false} tickLine={false} tick={{ fill: '#64748B', fontSize: 12 }} />
                    <Tooltip 
                      contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }}
                    />
                    <Line 
                      type="monotone" 
                      dataKey="wait" 
                      name="Wait Time (mins)"
                      stroke="#8B5CF6" 
                      strokeWidth={3}
                      dot={{ r: 4, fill: '#8B5CF6', strokeWidth: 2, stroke: '#fff' }}
                      activeDot={{ r: 6 }}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Data Table */}
        <Card>
          <CardHeader>
            <CardTitle>Recent Simulation Sessions</CardTitle>
            <CardDescription>Historical log runs and generated hospital stability scores.</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full text-sm text-left">
                <thead className="text-xs text-slate-500 uppercase bg-slate-50 dark:bg-slate-800/50">
                  <tr>
                    <th className="px-6 py-3 rounded-tl-lg">Date</th>
                    <th className="px-6 py-3">Scenario</th>
                    <th className="px-6 py-3">Duration (Sim Time)</th>
                    <th className="px-6 py-3">Final HSI</th>
                    <th className="px-6 py-3">Violations</th>
                    <th className="px-6 py-3 rounded-tr-lg">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                  <tr className="bg-white dark:bg-slate-900 border-b dark:border-slate-800">
                    <td className="px-6 py-4 font-medium text-slate-900 dark:text-white">Today, 10:45 AM</td>
                    <td className="px-6 py-4">MASS_CASUALTY</td>
                    <td className="px-6 py-4">4h 30m</td>
                    <td className="px-6 py-4 font-semibold text-orange-500">82.5</td>
                    <td className="px-6 py-4 text-slate-500">2</td>
                    <td className="px-6 py-4"><Button variant="ghost" size="sm" className="h-8">View Log</Button></td>
                  </tr>
                  <tr className="bg-white dark:bg-slate-900 border-b dark:border-slate-800">
                    <td className="px-6 py-4 font-medium text-slate-900 dark:text-white">Yesterday, 14:20 PM</td>
                    <td className="px-6 py-4">NORMAL</td>
                    <td className="px-6 py-4">24h 00m</td>
                    <td className="px-6 py-4 font-semibold text-green-500">98.0</td>
                    <td className="px-6 py-4 text-slate-500">0</td>
                    <td className="px-6 py-4"><Button variant="ghost" size="sm" className="h-8">View Log</Button></td>
                  </tr>
                  <tr className="bg-white dark:bg-slate-900">
                    <td className="px-6 py-4 font-medium text-slate-900 dark:text-white">Mar 15, 09:15 AM</td>
                    <td className="px-6 py-4">FLU_SURGE</td>
                    <td className="px-6 py-4">48h 00m</td>
                    <td className="px-6 py-4 font-semibold text-yellow-500">88.5</td>
                    <td className="px-6 py-4 text-slate-500">5</td>
                    <td className="px-6 py-4"><Button variant="ghost" size="sm" className="h-8">View Log</Button></td>
                  </tr>
                </tbody>
              </table>
            </div>
            
            <div className="mt-6 flex items-center justify-between text-sm text-slate-500">
              <p>Showing 3 of 24 logged sessions.</p>
              <p className="italic">Note: Integration with real-time log APIs is pending backend implementation.</p>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
