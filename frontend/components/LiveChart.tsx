'use client';

import {
    LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, AreaChart, Area
} from 'recharts';

export function LiveChart({ data }: { data: any[] }) {
    if (!data || data.length === 0) return <div className="h-[200px] flex items-center justify-center text-slate-400">Waiting for Data...</div>;

    // Transform last 20 points
    // Assume data is [ { time: 10, departments: {...} }, ... ]
    // But our API /metrics returns SINGLE state.
    // The frontend page needs to accumulate history or the backend needs to serve it.
    // The /metrics endpoint returns "recent_logs" but not time-series metrics efficiently yet.
    // Let's assume the PARENT passes specific history array or we visualize the "recent_logs" if relevant.

    // Actually, app/page.tsx needs to maintain a history buffer state for the chart.

    return (
        <ResponsiveContainer width="100%" height={300}>
            <AreaChart data={data}>
                <defs>
                    <linearGradient id="colorGeneral" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3} />
                        <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                    </linearGradient>
                    <linearGradient id="colorICU" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#a855f7" stopOpacity={0.3} />
                        <stop offset="95%" stopColor="#a855f7" stopOpacity={0} />
                    </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" className="stroke-slate-200 dark:stroke-slate-700" />
                <XAxis dataKey="time" className="text-xs" />
                <YAxis className="text-xs" />
                <Tooltip
                    contentStyle={{ backgroundColor: 'rgba(0,0,0,0.8)', color: '#fff', border: 'none', borderRadius: '8px' }}
                />
                <Legend />
                <Area
                    type="monotone"
                    dataKey="generalQueue"
                    name="General Queue"
                    stroke="#3b82f6"
                    fillOpacity={1}
                    fill="url(#colorGeneral)"
                    isAnimationActive={false}
                />
                <Area
                    type="monotone"
                    dataKey="icuQueue"
                    name="ICU Queue"
                    stroke="#a855f7"
                    fillOpacity={1}
                    fill="url(#colorICU)"
                    isAnimationActive={false}
                />
            </AreaChart>
        </ResponsiveContainer>
    );
}
