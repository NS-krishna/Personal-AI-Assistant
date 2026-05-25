/**
 * Sidebar — Left panel with app title, navigation, and recent memory.
 */

function Sidebar({ memory, onSelectQuery, activeView, onNavigate }) {
    const navItems = [
        { icon: '💬', label: 'Chat', view: 'chat' },
        { icon: '🧠', label: 'Memory', view: 'chat' },
        { icon: '📄', label: 'Upload', view: 'chat' },
        { icon: '📊', label: 'Health', view: 'dashboard' },
    ];

    return (
        <aside className="w-[220px] bg-[#0d0d14] border-r border-gray-800/60 flex flex-col shrink-0">
            {/* Logo / Title */}
            <div className="px-5 py-5 border-b border-gray-800/60">
                <div className="flex items-center gap-2.5">
                    <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-blue-500 to-violet-600 flex items-center justify-center text-lg">
                        🤖
                    </div>
                    <div>
                        <h1 className="text-sm font-bold text-white leading-tight">Personal AI</h1>
                        <p className="text-[10px] text-gray-500 font-medium">Agent v0.1</p>
                    </div>
                </div>
            </div>

            {/* Navigation */}
            <nav className="px-3 py-3 border-b border-gray-800/60 space-y-1">
                {navItems.map(item => {
                    const isActive = activeView === item.view;
                    return (
                        <button
                            key={item.label}
                            onClick={() => onNavigate(item.view)}
                            className={`w-full flex items-center gap-2.5 px-3 py-2 rounded-lg text-sm transition-colors ${isActive
                                    ? 'bg-gray-800/70 text-gray-200'
                                    : 'text-gray-400 hover:bg-gray-800/50 hover:text-gray-200'
                                }`}
                        >
                            <span className="text-base">{item.icon}</span>
                            {item.label}
                        </button>
                    );
                })}
            </nav>

            {/* Recent Conversations */}
            <div className="flex-1 overflow-y-auto px-3 py-3">
                <p className="text-[10px] font-semibold text-gray-600 uppercase tracking-wider px-3 mb-2">
                    Recent Memory
                </p>
                {memory.length === 0 && (
                    <p className="text-xs text-gray-600 px-3 italic">No conversations yet</p>
                )}
                {memory.map((item, i) => (
                    <button
                        key={i}
                        onClick={() => { onNavigate('chat'); onSelectQuery(item.user_message); }}
                        className="w-full text-left px-3 py-2 rounded-lg text-xs text-gray-500 hover:bg-gray-800/50 hover:text-gray-300 transition-colors truncate block mb-0.5"
                        title={item.user_message}
                    >
                        <span className="text-gray-600 mr-1.5">›</span>
                        {item.user_message}
                    </button>
                ))}
            </div>

            {/* Footer */}
            <div className="px-5 py-3 border-t border-gray-800/60">
                <p className="text-[10px] text-gray-700">
                    Powered by Groq + Ollama
                </p>
            </div>
        </aside>
    );
}

export default Sidebar;
