'use client';

import { useState } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Settings, UserPlus, ArrowLeft, Save } from 'lucide-react';
import Link from 'next/link';

export default function SettingsPage() {
    // Config State
    const [config, setConfig] = useState({
        beds: 50,
        icu_beds: 10,
        staff: 20,
        arrival_rate: 0.5,
        use_rl: false
    });

    // Patient State
    const [patient, setPatient] = useState({
        severity: 3,
        care_type: 'General'
    });

    const [msg, setMsg] = useState('');

    const handleConfigChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        setConfig({ ...config, [e.target.name]: parseFloat(e.target.value) });
    };

    const applyConfig = async () => {
        try {
            const res = await fetch('http://localhost:8001/simulation/reset', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(config)
            });
            if (res.ok) setMsg("✅ Simulation Reset with New Config!");
        } catch (e) {
            setMsg("❌ Error applying config");
        }
    };

    const admitPatient = async () => {
        try {
            const res = await fetch('http://localhost:8001/simulation/admit', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(patient)
            });
            if (res.ok) setMsg("✅ Patient Admitted!");
        } catch (e) {
            setMsg("❌ Error admitting patient");
        }
    };

    return (
        <div className="min-h-screen bg-slate-50 dark:bg-black p-8 font-sans">
            <div className="mb-8 flex items-center gap-4">
                <Link href="/">
                    <Button variant="outline" size="icon">
                        <ArrowLeft className="w-5 h-5" />
                    </Button>
                </Link>
                <h1 className="text-3xl font-bold tracking-tight text-slate-900 dark:text-white">Simulation Settings</h1>
            </div>

            {msg && <div className="mb-4 p-4 bg-blue-100 text-blue-800 rounded-lg">{msg}</div>}

            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                {/* Configuration Card */}
                <Card>
                    <CardHeader>
                        <CardTitle className="flex items-center gap-2">
                            <Settings className="w-5 h-5" /> Global Parameters
                        </CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-4">
                        <div className="space-y-2">
                            <label className="text-sm font-medium">General Beds ({config.beds})</label>
                            <input type="range" name="beds" min="10" max="200" value={config.beds} onChange={handleConfigChange} className="w-full" />
                        </div>
                        <div className="space-y-2">
                            <label className="text-sm font-medium">ICU Beds ({config.icu_beds})</label>
                            <input type="range" name="icu_beds" min="2" max="50" value={config.icu_beds} onChange={handleConfigChange} className="w-full" />
                        </div>
                        <div className="space-y-2">
                            <label className="text-sm font-medium">Total Staff ({config.staff})</label>
                            <input type="range" name="staff" min="5" max="100" value={config.staff} onChange={handleConfigChange} className="w-full" />
                        </div>
                        <div className="space-y-2">
                            <label className="text-sm font-medium">Arrival Rate ({config.arrival_rate} patients/hr)</label>
                            <input type="range" name="arrival_rate" min="0.1" max="5.0" step="0.1" value={config.arrival_rate} onChange={handleConfigChange} className="w-full" />
                        </div>

                        <div className="flex items-center space-x-2 pt-4 border-t border-slate-100">
                            <input
                                type="checkbox"
                                id="use_rl"
                                checked={config.use_rl}
                                onChange={(e) => setConfig({ ...config, use_rl: e.target.checked })}
                                className="w-5 h-5 text-blue-600 rounded focus:ring-blue-500"
                            />
                            <label htmlFor="use_rl" className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70">
                                Enable AI Agent (PPO Model)
                            </label>
                        </div>

                        <Button onClick={applyConfig} className="w-full mt-4">
                            <Save className="w-4 h-4 mr-2" /> Apply & Reset Simulation
                        </Button>
                    </CardContent>
                </Card>

                {/* Manual Admission Card */}
                <Card>
                    <CardHeader>
                        <CardTitle className="flex items-center gap-2">
                            <UserPlus className="w-5 h-5" /> Manual Entry
                        </CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-4">
                        <p className="text-sm text-slate-500">Inject a specific patient case.</p>

                        <div className="space-y-2">
                            <label className="text-sm font-medium">Care Type</label>
                            <select
                                className="w-full p-2 border rounded-md"
                                value={patient.care_type}
                                onChange={(e) => setPatient({ ...patient, care_type: e.target.value })}
                            >
                                <option value="General">General Ward</option>
                                <option value="ICU">ICU (Critical)</option>
                                <option value="Emergency">Emergency</option>
                            </select>
                        </div>

                        <div className="space-y-2">
                            <label className="text-sm font-medium">Severity (1-5)</label>
                            <div className="flex gap-2">
                                {[1, 2, 3, 4, 5].map(s => (
                                    <button
                                        key={s}
                                        onClick={() => setPatient({ ...patient, severity: s })}
                                        className={`px-4 py-2 rounded-md border ${patient.severity === s ? 'bg-blue-500 text-white' : 'bg-white'}`}
                                    >
                                        {s}
                                    </button>
                                ))}
                            </div>
                        </div>

                        <Button onClick={admitPatient} className="w-full mt-4 bg-green-600 hover:bg-green-700">
                            <UserPlus className="w-4 h-4 mr-2" /> Admit Patient
                        </Button>
                    </CardContent>
                </Card>
            </div>
        </div>
    );
}
