"use client";

import { useState, useEffect } from 'react';
import { Clock, Calendar } from 'lucide-react';

interface TimeControlProps {
    onChange: (timestamp: string) => void;
}

export default function TimeControl({ onChange }: TimeControlProps) {
    const [value, setValue] = useState(100);
    const [currentDate, setCurrentDate] = useState<Date>(new Date());

    // Calculate date range: 1 year ago to now
    const now = new Date().getTime();
    const oneYearAgo = new Date().setFullYear(new Date().getFullYear() - 1);
    const range = now - oneYearAgo;

    const handleSliderChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const percent = parseInt(e.target.value);
        setValue(percent);

        // Calculate timestamp based on percentage
        const timestamp = oneYearAgo + (range * (percent / 100));
        const date = new Date(timestamp);
        setCurrentDate(date);

        // Emit ISO string
        onChange(date.toISOString());
    };

    // Initial emit on mount
    useEffect(() => {
        onChange(new Date().toISOString());
    }, []);

    return (
        <div className="bg-slate-800 p-4 rounded-lg border border-slate-700 shadow-lg w-full max-w-2xl mx-auto">
            <div className="flex items-center justify-between mb-2 text-slate-200">
                <div className="flex items-center gap-2">
                    <Clock className="w-5 h-5 text-blue-400" />
                    <span className="font-semibold">Time Travel</span>
                </div>
                <div className="flex items-center gap-2 text-sm bg-slate-900 px-3 py-1 rounded-full border border-slate-700">
                    <Calendar className="w-4 h-4 text-emerald-400" />
                    <span className="font-mono text-emerald-300">
                        {currentDate.toLocaleString()}
                    </span>
                </div>
            </div>

            <div className="relative pt-1">
                <input
                    type="range"
                    min="0"
                    max="100"
                    value={value}
                    onChange={handleSliderChange}
                    className="w-full h-2 bg-slate-700 rounded-lg appearance-none cursor-pointer accent-blue-500 hover:accent-blue-400 transition-all"
                />
                <div className="flex justify-between text-xs text-slate-500 mt-2 font-mono">
                    <span>1 Year Ago</span>
                    <span>Now</span>
                </div>
            </div>
        </div>
    );
}
