/**
 * RightPanel — Health status + quick action buttons.
 */

function RightPanel({ health, quickActions, onQuickAction, onClearMemory }) {
    return (
        <aside className="w-[250px] bg-[#0d0d14] border-l border-gray-800/60 flex flex-col shrink-0">
            {/* Health Status */}
            <div className="px-5 py-4 border-b border-gray-800/60">
                <p className="text-[10px] font-semibold text-gray-600 uppercase tracking-wider mb-3">
                    Service Health
                </p>
                <div className="space-y-2.5">
                    <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                            <span className={`w-2 h-2 rounded-full ${health.ollama ? 'bg-emerald-400 shadow-sm shadow-emerald-400/50' : 'bg-red-400 shadow-sm shadow-red-400/50'}`}></span>
                            <span className="text-xs text-gray-400">Ollama</span>
                        </div>
                        <span className="text-[10px] text-gray-600">{health.ollama ? 'Connected' : 'Offline'}</span>
                    </div>
                    <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                            <span className={`w-2 h-2 rounded-full ${health.groq ? 'bg-emerald-400 shadow-sm shadow-emerald-400/50' : 'bg-red-400 shadow-sm shadow-red-400/50'}`}></span>
                            <span className="text-xs text-gray-400">Groq</span>
                        </div>
                        <span className="text-[10px] text-gray-600">{health.groq ? 'Connected' : 'Offline'}</span>
                    </div>
                </div>
            </div>

            {/* Quick Actions */}
            <div className="flex-1 px-4 py-4">
                <p className="text-[10px] font-semibold text-gray-600 uppercase tracking-wider px-1 mb-3">
                    Quick Actions
                </p>
                <div className="space-y-2">
                    {quickActions.map((action, i) => (
                        <button
                            key={i}
                            onClick={() => onQuickAction(action.query)}
                            className="w-full flex items-center gap-2.5 px-3 py-2.5 rounded-xl bg-gray-800/40 border border-gray-800/60 text-sm text-gray-400 hover:bg-gray-800 hover:text-gray-200 hover:border-gray-700 transition-all text-left"
                        >
                            <span className="text-base shrink-0">{action.icon}</span>
                            <span className="text-xs">{action.label}</span>
                        </button>
                    ))}

                    {/* Clear Memory — destructive action */}
                    <button
                        onClick={onClearMemory}
                        className="w-full flex items-center gap-2.5 px-3 py-2.5 rounded-xl bg-red-900/10 border border-red-900/20 text-sm text-red-400/70 hover:bg-red-900/20 hover:text-red-400 hover:border-red-800/40 transition-all text-left mt-4"
                    >
                        <span className="text-base shrink-0">🗑️</span>
                        <span className="text-xs">Clear Memory</span>
                    </button>
                </div>
            </div>

            {/* Model info footer */}
            <div className="px-5 py-3 border-t border-gray-800/60">
                <div className="space-y-1">
                    <div className="flex justify-between text-[10px]">
                        <span className="text-gray-600">Local</span>
                        <span className="text-gray-500">qwen2.5-coder</span>
                    </div>
                    <div className="flex justify-between text-[10px]">
                        <span className="text-gray-600">Cloud</span>
                        <span className="text-gray-500">llama-3.3-70b</span>
                    </div>
                </div>
            </div>
        </aside>
    );
}

export default RightPanel;
