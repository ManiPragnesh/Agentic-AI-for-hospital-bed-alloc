'use client';

import { useState } from 'react';
import { Send, Bot, Loader2, Globe } from 'lucide-react';
import ReactMarkdown from 'react-markdown';

export function AdvisorPanel() {
    const [response, setResponse] = useState('');
    const [loading, setLoading] = useState(false);

    const handleAskAI = async () => {
        setLoading(true);
        setResponse(""); // Clear previous

        try {
            const res = await fetch('http://127.0.0.1:8000/api/analyze/advisor', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ api_key: "OFFLINE_MODE" }),
            });

            if (!res.body) return;
            const reader = res.body.getReader();
            const decoder = new TextDecoder();
            let done = false;

            while (!done) {
                const { value, done: doneReading } = await reader.read();
                done = doneReading;
                const chunkValue = decoder.decode(value);
                setResponse((prev) => prev + chunkValue);
            }
        } catch (e) {
            setResponse("❌ Error connecting to Local AI Advisor.");
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="bg-gradient-to-br from-indigo-600 to-purple-700 rounded-xl text-white shadow-lg overflow-hidden flex flex-col h-[500px]">
            <div className="p-6 pb-4 border-b border-white/10">
                <div className="flex justify-between items-start">
                    <div>
                        <h3 className="font-bold text-lg flex items-center gap-2">
                            <Bot className="w-5 h-5" /> Agentic Strategy Engine
                        </h3>
                        <p className="text-indigo-100 text-xs mt-1">
                            Operational Resource Optimization (Offline)
                        </p>
                    </div>
                    <div className="flex items-center gap-1 bg-green-500/20 text-green-300 px-2 py-1 rounded-full text-[10px] uppercase font-bold tracking-wider">
                        <Globe className="w-3 h-3" /> Local Mode
                    </div>
                </div>
            </div>

            {/* Chat Area */}
            <div className="flex-1 p-4 overflow-y-auto bg-black/10 text-sm space-y-4">
                {response ? (
                    <div className="prose prose-invert prose-sm max-w-none">
                        <ReactMarkdown>{response}</ReactMarkdown>
                    </div>
                ) : (
                    <div className="flex flex-col items-center justify-center h-full text-center text-white/40 space-y-4">
                        <div className="p-4 bg-white/5 rounded-full">
                            <Bot className="w-8 h-8 opacity-20" />
                        </div>
                        <p className="text-xs max-w-[200px]">
                            Click the button below to generate a real-time strategic analysis of the current hospital state.
                        </p>
                    </div>
                )}
            </div>

            {/* Controls */}
            <div className="p-4 bg-black/20">
                <button
                    onClick={handleAskAI}
                    disabled={loading}
                    className="w-full py-3 bg-white text-indigo-700 hover:bg-slate-100 disabled:opacity-50 disabled:cursor-not-allowed rounded-xl text-sm font-bold transition-all shadow-lg active:scale-[0.98] flex items-center justify-center gap-2"
                >
                    {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
                    {loading ? 'Analyzing Hospital State...' : 'Generate Strategic Analysis'}
                </button>
            </div>
        </div>
    );
}
