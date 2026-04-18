'use client';

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { AlertCircle, CheckCircle2 } from "lucide-react";

export default function ResourceOptimizationPage() {
  const [careType, setCareType] = useState("General");
  const [severity, setSeverity] = useState(3);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<{ text: string; type: 'success' | 'error' } | null>(null);

  const handleAdmit = async () => {
    setLoading(true);
    setMessage(null);
    try {
      const res = await fetch('http://127.0.0.1:8000/api/simulation/admit', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          care_type: careType,
          severity: severity
        })
      });
      
      const data = await res.json();
      
      if (res.ok) {
        setMessage({ text: data.message || "Patient successfully joined the queue.", type: 'success' });
      } else {
        setMessage({ text: data.detail || "Failed to admit patient.", type: 'error' });
      }
    } catch (e: any) {
      setMessage({ text: "Network error occurred while connecting to the simulation.", type: 'error' });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-black p-8">
      <div className="max-w-6xl mx-auto space-y-8">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-slate-900 dark:text-white">
            Resource Optimization
          </h1>
          <p className="mt-2 text-slate-600 dark:text-slate-300">
            Hospital resource allocation and optimization. Manually inject specific patient cases into the simulation queue to observe responses.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <Card>
            <CardHeader>
              <CardTitle>Manual Entry</CardTitle>
              <CardDescription>Inject a specific patient case into the live simulation.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              
              {message && (
                <div className={`p-4 rounded-md flex items-start gap-3 text-sm ${message.type === 'success' ? 'bg-green-50 text-green-800 dark:bg-green-900/20 dark:text-green-400' : 'bg-red-50 text-red-800 dark:bg-red-900/20 dark:text-red-400'}`}>
                  {message.type === 'success' ? <CheckCircle2 className="w-5 h-5 shrink-0" /> : <AlertCircle className="w-5 h-5 shrink-0" />}
                  <p className="pt-0.5">{message.text}</p>
                </div>
              )}

              <div className="space-y-2">
                <label className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70 text-slate-700 dark:text-slate-300">
                  Care Type
                </label>
                <select 
                  className="flex h-10 w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-slate-400 dark:border-slate-800 dark:bg-slate-950 dark:text-slate-50"
                  value={careType}
                  onChange={(e) => setCareType(e.target.value)}
                >
                  <option value="General">General Ward</option>
                  <option value="ICU">Intensive Care Unit (ICU)</option>
                  <option value="Emergency">Emergency</option>
                </select>
              </div>

              <div className="space-y-3">
                <div className="flex justify-between items-center">
                  <label className="text-sm font-medium leading-none text-slate-700 dark:text-slate-300">
                    Severity (1-5)
                  </label>
                  <span className="text-sm font-bold text-blue-600 dark:text-blue-400">{severity}</span>
                </div>
                
                <div className="flex justify-between gap-2">
                  {[1, 2, 3, 4, 5].map((level) => (
                    <button
                      key={level}
                      onClick={() => setSeverity(level)}
                      className={`flex-1 h-10 rounded-md border transition-all duration-200 ${
                        severity === level 
                        ? 'border-blue-600 bg-blue-50 text-blue-700 font-semibold dark:bg-blue-900/30 dark:border-blue-500 dark:text-blue-300' 
                        : 'border-slate-200 bg-white text-slate-600 hover:bg-slate-50 dark:border-slate-800 dark:bg-slate-950 dark:text-slate-400 dark:hover:bg-slate-900'
                      }`}
                    >
                      {level}
                    </button>
                  ))}
                </div>
                <p className="text-xs text-slate-500 dark:text-slate-400 text-center flex justify-between px-2">
                  <span>Very Low</span>
                  <span>Critical</span>
                </p>
              </div>

              <Button 
                onClick={handleAdmit} 
                disabled={loading}
                className="w-full bg-blue-600 hover:bg-blue-700 text-white"
              >
                {loading ? "Injecting..." : "Admit Patient"}
              </Button>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
