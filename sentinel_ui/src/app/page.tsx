"use client";

import { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import { Activity, Database, Network, Search } from 'lucide-react';
import GraphVisualization from '../components/GraphVisualization';
import TimeControl from '../components/TimeControl';

// API Base URL - in production this should be env var
const API_URL = 'http://localhost:8000';

export default function Home() {
    const [graphData, setGraphData] = useState({ nodes: [], links: [] });
    const [loading, setLoading] = useState(false);
    const [urlInput, setUrlInput] = useState('');
    const [jobStatus, setJobStatus] = useState<string | null>(null);

    // Fetch graph history
    const fetchGraphHistory = useCallback(async (timestamp: string) => {
        try {
            // Don't set loading true here to avoid flickering on slider drag
            const response = await axios.get(`${API_URL}/graph/history`, {
                params: { timestamp }
            });
            setGraphData(response.data);
        } catch (error) {
            console.error("Failed to fetch graph history:", error);
        }
    }, []);

    // Submit new job
    const submitJob = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!urlInput) return;

        try {
            setJobStatus('Submitting...');
            const response = await axios.post(`${API_URL}/job`, { url: urlInput });
            setJobStatus(`Job submitted! Task ID: ${response.data.task_id}`);
            setUrlInput('');

            // Clear status after 3 seconds
            setTimeout(() => setJobStatus(null), 3000);
        } catch (error) {
            console.error("Failed to submit job:", error);
            setJobStatus('Failed to submit job');
        }
    };

    return (
        <main className="flex min-h-screen flex-col bg-slate-950 text-slate-100">
            {/* Header */}
            <header className="border-b border-slate-800 bg-slate-900/50 backdrop-blur-sm sticky top-0 z-10">
                <div className="container mx-auto px-4 h-16 flex items-center justify-between">
                    <div className="flex items-center gap-2">
                        <Network className="w-6 h-6 text-blue-500" />
                        <h1 className="text-xl font-bold bg-gradient-to-r from-blue-400 to-emerald-400 bg-clip-text text-transparent">
                            Sentinel Platform
                        </h1>
                    </div>

                    <div className="flex items-center gap-4 text-sm text-slate-400">
                        <div className="flex items-center gap-1">
                            <Database className="w-4 h-4" />
                            <span>Neo4j Connected</span>
                        </div>
                        <div className="flex items-center gap-1">
                            <Activity className="w-4 h-4 text-emerald-500" />
                            <span>System Healthy</span>
                        </div>
                    </div>
                </div>
            </header>

            {/* Main Content */}
            <div className="flex-1 container mx-auto px-4 py-6 flex flex-col gap-6">

                {/* Job Submission */}
                <div className="bg-slate-900 p-4 rounded-lg border border-slate-800">
                    <form onSubmit={submitJob} className="flex gap-4">
                        <div className="relative flex-1">
                            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
                            <input
                                type="url"
                                placeholder="Enter URL to process..."
                                value={urlInput}
                                onChange={(e) => setUrlInput(e.target.value)}
                                className="w-full bg-slate-950 border border-slate-700 rounded-md py-2 pl-10 pr-4 text-slate-200 focus:outline-none focus:ring-2 focus:ring-blue-500"
                            />
                        </div>
                        <button
                            type="submit"
                            disabled={!urlInput}
                            className="bg-blue-600 hover:bg-blue-500 text-white px-6 py-2 rounded-md font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                            Process
                        </button>
                    </form>
                    {jobStatus && (
                        <div className="mt-2 text-sm text-emerald-400 font-mono">
                            {jobStatus}
                        </div>
                    )}
                </div>

                {/* Graph Visualization Area */}
                <div className="flex-1 relative min-h-[500px] flex flex-col gap-4">
                    <GraphVisualization data={graphData} />

                    {/* Floating Time Control */}
                    <div className="absolute bottom-6 left-1/2 -translate-x-1/2 w-full max-w-2xl px-4">
                        <TimeControl onChange={fetchGraphHistory} />
                    </div>
                </div>
            </div>
        </main>
    );
}
