/**
 * EvalDashboard — Evaluation metrics dashboard.
 *
 * Shows stat cards, tool usage bar chart, and score-over-time line chart.
 * Fetches data from GET /evaluation/stats.
 */

import { useState, useEffect } from 'react';

const API = 'http://localhost:8000';

const TOOL_COLORS = {
    gmail_reader: '#60a5fa',
    calendar: '#a78bfa',
    summarizer: '#34d399',
    chat: '#fbbf24',
    rag_search: '#f472b6',
    doc_summarizer: '#fb923c',
};

function EvalDashboard() {
    const [stats, setStats] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetch(`${API}/evaluation/stats`)
            .then(r => r.json())
            .then(d => { setStats(d); setLoading(false); })
            .catch(() => setLoading(false));
    }, []);

    if (loading) {
        return (
            <div className="flex-1 flex items-center justify-center">
                <div className="text-gray-500 text-sm">Loading evaluation data...</div>
            </div>
        );
    }

    if (!stats || stats.total_conversations === 0) {
        return (
            <div className="flex-1 flex flex-col items-center justify-center text-center px-8">
                <div className="text-5xl mb-4">📊</div>
                <h2 className="text-xl font-bold text-gray-300 mb-2">No Data Yet</h2>
                <p className="text-sm text-gray-500 max-w-md">
                    Start chatting with the AI agent to collect evaluation metrics.
                    Stats will appear here after your first conversation.
                </p>
            </div>
        );
    }

    const { total_conversations, average_score, total_retries, avg_response_time_ms, tool_usage, scores_over_time } = stats;

    // Tool usage as sorted array for bar chart
    const totalToolUses = Object.values(tool_usage).reduce((a, b) => a + b, 0);
    const toolEntries = Object.entries(tool_usage)
        .sort(([, a], [, b]) => b - a)
        .map(([tool, count]) => ({
            tool,
            count,
            pct: totalToolUses > 0 ? Math.round((count / totalToolUses) * 100) : 0,
            color: TOOL_COLORS[tool] || '#94a3b8',
        }));

    // Score chart SVG dimensions
    const chartW = 500, chartH = 160, padX = 40, padY = 20;
    const innerW = chartW - padX * 2;
    const innerH = chartH - padY * 2;

    const scorePoints = scores_over_time.length > 1
        ? scores_over_time.map((pt, i) => {
            const x = padX + (i / (scores_over_time.length - 1)) * innerW;
            const y = padY + innerH - (pt.avg_score / 10) * innerH;
            return { x, y, ...pt };
        })
        : scores_over_time.length === 1
            ? [{ x: chartW / 2, y: padY + innerH - (scores_over_time[0].avg_score / 10) * innerH, ...scores_over_time[0] }]
            : [];

    const polylinePoints = scorePoints.map(p => `${p.x},${p.y}`).join(' ');

    return (
        <div className="flex-1 flex flex-col min-w-0 overflow-y-auto">
            {/* Header */}
            <div className="h-14 px-6 flex items-center border-b border-gray-800/60 bg-[#0d0d14]/80 backdrop-blur-sm shrink-0">
                <h2 className="text-sm font-semibold text-gray-300">Evaluation Dashboard</h2>
            </div>

            <div className="px-6 py-6 space-y-6 max-w-4xl mx-auto w-full">
                {/* Row 1: Stat Cards */}
                <div className="grid grid-cols-4 gap-4">
                    <StatCard
                        label="Total Conversations"
                        value={total_conversations}
                        icon="💬"
                        color="from-blue-600/20 to-blue-500/10"
                        border="border-blue-500/20"
                    />
                    <StatCard
                        label="Average Score"
                        value={`${average_score}/10`}
                        icon="⭐"
                        color="from-amber-600/20 to-amber-500/10"
                        border="border-amber-500/20"
                    />
                    <StatCard
                        label="Total Retries"
                        value={total_retries}
                        icon="🔄"
                        color="from-red-600/20 to-red-500/10"
                        border="border-red-500/20"
                    />
                    <StatCard
                        label="Avg Response Time"
                        value={`${(avg_response_time_ms / 1000).toFixed(1)}s`}
                        icon="⏱️"
                        color="from-emerald-600/20 to-emerald-500/10"
                        border="border-emerald-500/20"
                    />
                </div>

                {/* Row 2: Tool Usage */}
                <div className="bg-gray-800/40 border border-gray-800/60 rounded-2xl p-5">
                    <h3 className="text-sm font-semibold text-gray-300 mb-4">Tool Usage</h3>
                    <div className="space-y-3">
                        {toolEntries.map(({ tool, count, pct, color }) => (
                            <div key={tool} className="flex items-center gap-3">
                                <span className="text-xs text-gray-400 w-28 text-right truncate">{tool}</span>
                                <div className="flex-1 h-6 bg-gray-900/60 rounded-full overflow-hidden">
                                    <div
                                        className="h-full rounded-full transition-all duration-700 ease-out flex items-center px-2"
                                        style={{ width: `${Math.max(pct, 4)}%`, backgroundColor: color }}
                                    >
                                        <span className="text-[10px] font-bold text-white/90 whitespace-nowrap">
                                            {count} ({pct}%)
                                        </span>
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                    {toolEntries.length === 0 && (
                        <p className="text-xs text-gray-600 italic">No tool usage data yet.</p>
                    )}
                </div>

                {/* Row 3: Score Over Time */}
                <div className="bg-gray-800/40 border border-gray-800/60 rounded-2xl p-5">
                    <h3 className="text-sm font-semibold text-gray-300 mb-4">Score Over Time</h3>
                    {scorePoints.length > 0 ? (
                        <svg viewBox={`0 0 ${chartW} ${chartH}`} className="w-full" style={{ maxHeight: '200px' }}>
                            {/* Grid lines */}
                            {[0, 2, 4, 6, 8, 10].map(v => {
                                const y = padY + innerH - (v / 10) * innerH;
                                return (
                                    <g key={v}>
                                        <line x1={padX} y1={y} x2={chartW - padX} y2={y} stroke="#1e293b" strokeWidth="1" />
                                        <text x={padX - 8} y={y + 4} textAnchor="end" fill="#64748b" fontSize="10">{v}</text>
                                    </g>
                                );
                            })}

                            {/* Gradient fill under line */}
                            {scorePoints.length > 1 && (
                                <>
                                    <defs>
                                        <linearGradient id="scoreGrad" x1="0" y1="0" x2="0" y2="1">
                                            <stop offset="0%" stopColor="#3b82f6" stopOpacity="0.3" />
                                            <stop offset="100%" stopColor="#3b82f6" stopOpacity="0" />
                                        </linearGradient>
                                    </defs>
                                    <polygon
                                        points={`${scorePoints[0].x},${padY + innerH} ${polylinePoints} ${scorePoints[scorePoints.length - 1].x},${padY + innerH}`}
                                        fill="url(#scoreGrad)"
                                    />
                                    <polyline
                                        points={polylinePoints}
                                        fill="none"
                                        stroke="#3b82f6"
                                        strokeWidth="2.5"
                                        strokeLinecap="round"
                                        strokeLinejoin="round"
                                    />
                                </>
                            )}

                            {/* Data points */}
                            {scorePoints.map((pt, i) => (
                                <g key={i}>
                                    <circle cx={pt.x} cy={pt.y} r="4" fill="#3b82f6" stroke="#0a0a0f" strokeWidth="2" />
                                    <text x={pt.x} y={padY + innerH + 14} textAnchor="middle" fill="#64748b" fontSize="9">
                                        {pt.date.slice(5)}
                                    </text>
                                    <text x={pt.x} y={pt.y - 10} textAnchor="middle" fill="#93c5fd" fontSize="10" fontWeight="bold">
                                        {pt.avg_score}
                                    </text>
                                </g>
                            ))}
                        </svg>
                    ) : (
                        <p className="text-xs text-gray-600 italic">Need at least one conversation to show the chart.</p>
                    )}
                </div>
            </div>
        </div>
    );
}

function StatCard({ label, value, icon, color, border }) {
    return (
        <div className={`bg-gradient-to-br ${color} border ${border} rounded-2xl p-4 animate-fade-in`}>
            <div className="flex items-center justify-between mb-2">
                <span className="text-lg">{icon}</span>
            </div>
            <div className="text-2xl font-bold text-white mb-0.5">{value}</div>
            <div className="text-[11px] text-gray-400">{label}</div>
        </div>
    );
}

export default EvalDashboard;
