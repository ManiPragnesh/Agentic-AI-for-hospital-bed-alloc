'use client';

import { useState } from 'react';
import { Send, Bot, Loader2 } from 'lucide-react';
import { Card } from '@/components/ui/card';
import ReactMarkdown from 'react-markdown';

export function AdvisorPanel() {
    const [apiKey, setApiKey] = useState('');
    const [response, setResponse] = useState('');
    const [loading, setLoading] = useState(false);

    const handleAskAI = async () => {
        if (!apiKey) {
            setResponse("⚠️ Please enter your OpenAI API Key first.");
            return;
        }

        setLoading(true);
        setResponse(""); // Clear previous

        try {
            const res = await fetch('http://localhost:8001/analyze/advisor', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ api_key: apiKey }),
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
            setResponse("❌ Error connecting to AI Advisor.");
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="bg-gradient-to-br from-indigo-500 to-purple-600 rounded-xl text-white shadow-lg overflow-hidden flex flex-col h-[500px]">
            <div className="p-6 pb-4 border-b border-white/10">
                <h3 className="font-bold text-lg flex items-center gap-2">
                    <Bot className="w-5 h-5" /> AI Strategic Advisor
                </h3>
                <p className="text-indigo-100 text-xs mt-1">
                    Powered by OpenAI GPT-3.5
                </p>
            </div>

            {/* Chat Area */}
            <div className="flex-1 p-4 overflow-y-auto bg-black/10 text-sm space-y-4">
                {response ? (
                    <div className="prose prose-invert prose-sm max-w-none">
                        <ReactMarkdown>{response}</ReactMarkdown>
                    </div>
                ) : (
                    <div className="text-center text-white/40 mt-10">
                        Enter API Key and click "Generate Analysis" to get real-time strategic advice.
                    </div>
                )}
            </div>

            {/* Controls */}
            <div className="p-4 bg-black/20 space-y-3">
                <input
                    type="password"
                    placeholder="OpenAI API Key (sk-...)"
                    value={apiKey}
                    onChange={(e) => setApiKey(e.target.value)}
                    className="w-full px-3 py-2 bg-black/20 border border-white/10 rounded-lg text-xs text-white placeholder:text-white/30 focus:outline-none focus:border-white/50"
                />

                <button
                    onClick={handleAskAI}
                    disabled={loading}
                    className="w-full py-2 bg-white text-indigo-600 hover:bg-indigo-50 rounded-lg text-sm font-bold transition-colors flex items-center justify-center gap-2"
                >
                    {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
                    {loading ? 'Analyzing...' : 'Generate Analysis'}
                </button>
            </div>
        </div>
    );
}
