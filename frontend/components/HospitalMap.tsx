'use client';

import { motion } from "framer-motion";

interface DeptProps {
    name: string;
    queue: number;
    occupancy: number;
    capacity: number;
    active: boolean; // Is processing patients?
    color: string;
}

const DepartmentNode = ({ name, queue, occupancy, capacity, active, color }: DeptProps) => {
    // Occupancy Percentage
    const occPct = (occupancy / capacity) * 100;

    return (
        <motion.div
            layout
            className={`p-4 rounded-xl border-2 ${color} bg-white dark:bg-slate-900 shadow-sm relative overflow-hidden`}
        >
            {/* Background Fill Level */}
            <div
                className={`absolute bottom-0 left-0 w-full opacity-10 transition-all duration-500`}
                style={{ height: `${occPct}%`, backgroundColor: 'currentColor' }}
            />

            <div className="flex justify-between items-center mb-2">
                <h4 className="font-bold text-lg">{name}</h4>
                <div className={`w-3 h-3 rounded-full ${active ? 'bg-green-500 animate-pulse' : 'bg-slate-300'}`} />
            </div>

            <div className="grid grid-cols-2 gap-2 text-sm">
                <div>
                    <span className="text-slate-500 block text-xs">Queue</span>
                    <span className="font-mono font-bold text-lg">{queue}</span>
                </div>
                <div>
                    <span className="text-slate-500 block text-xs">Beds</span>
                    <span className="font-mono">{occupancy}/{capacity}</span>
                </div>
            </div>

            {/* Queue Visuals (Dots) */}
            <div className="mt-3 flex flex-wrap gap-1 h-6 overflow-hidden">
                {Array.from({ length: Math.min(queue, 20) }).map((_, i) => (
                    <motion.div
                        key={i}
                        initial={{ scale: 0 }}
                        animate={{ scale: 1 }}
                        className="w-1.5 h-1.5 rounded-full bg-red-400"
                    />
                ))}
                {queue > 20 && <span className="text-xs text-slate-400">+{queue - 20}</span>}
            </div>
        </motion.div>
    );
};

export function HospitalMap({ data }: { data: any }) {
    if (!data) return <div className="p-10 text-center text-slate-400">Loading Hospital Map...</div>;

    const depts = data.departments || {};

    return (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-2 gap-4">
            {/* Emergency (Entry Point) */}
            <DepartmentNode
                name="Emergency"
                queue={depts['Emergency']?.queue_length || 0}
                occupancy={depts['Emergency']?.occupancy || 0}
                capacity={depts['Emergency']?.capacity || 10}
                active={depts['Emergency']?.staff_active > 0}
                color="border-red-500 text-red-500"
            />

            {/* ICU (Critical) */}
            <DepartmentNode
                name="ICU"
                queue={depts['ICU']?.queue_length || 0}
                occupancy={depts['ICU']?.occupancy || 0}
                capacity={depts['ICU']?.capacity || 10}
                active={depts['ICU']?.staff_active > 0}
                color="border-purple-500 text-purple-500"
            />

            {/* General Ward */}
            <DepartmentNode
                name="General Ward"
                queue={depts['General']?.queue_length || 0}
                occupancy={depts['General']?.occupancy || 0}
                capacity={depts['General']?.capacity || 50}
                active={depts['General']?.staff_active > 0}
                color="border-blue-500 text-blue-500"
            />

            {/* Maternity (Specific) */}
            <DepartmentNode
                name="Maternity"
                queue={depts['Maternity']?.queue_length || 0}
                occupancy={depts['Maternity']?.occupancy || 0}
                capacity={depts['Maternity']?.capacity || 15}
                active={depts['Maternity']?.staff_active > 0}
                color="border-pink-500 text-pink-500"
            />
        </div>
    );
}
