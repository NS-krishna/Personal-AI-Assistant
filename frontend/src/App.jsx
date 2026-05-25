import { useState, useEffect, useCallback } from 'react';
import Sidebar from './components/Sidebar';
import ChatWindow from './components/ChatWindow';
import RightPanel from './components/RightPanel';
import EvalDashboard from './components/EvalDashboard';

const API = 'http://localhost:8000';

function App() {
    const [messages, setMessages] = useState([]);
    const [loading, setLoading] = useState(false);
    const [health, setHealth] = useState({ ollama: false, groq: false });
    const [memory, setMemory] = useState([]);
    const [activeView, setActiveView] = useState('chat');

    // ── Fetch health on mount ──────────────────────────────────────────
    useEffect(() => {
        fetch(`${API}/health`)
            .then(r => r.json())
            .then(d => setHealth({ ollama: d.ollama, groq: d.groq }))
            .catch(() => { });
        fetchMemory();
    }, []);

    const fetchMemory = () => {
        fetch(`${API}/memory`)
            .then(r => r.json())
            .then(d => setMemory(d.conversations || []))
            .catch(() => { });
    };

    // ── Send chat message ──────────────────────────────────────────────
    const sendMessage = useCallback(async (text) => {
        if (!text.trim()) return;

        const userMsg = { role: 'user', content: text, timestamp: new Date().toISOString() };
        setMessages(prev => [...prev, userMsg]);
        setLoading(true);

        try {
            const res = await fetch(`${API}/chat`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ text }),
            });
            const data = await res.json();

            const aiMsg = {
                role: 'assistant',
                content: data.reply,
                plan: data.plan,
                score: data.score,
                feedback: data.feedback,
                timestamp: new Date().toISOString(),
            };
            setMessages(prev => [...prev, aiMsg]);
            fetchMemory();
        } catch (err) {
            setMessages(prev => [...prev, {
                role: 'assistant',
                content: `⚠️ Error: ${err.message}`,
                timestamp: new Date().toISOString(),
            }]);
        } finally {
            setLoading(false);
        }
    }, []);

    // ── Stream chat message ────────────────────────────────────────────
    const sendStream = useCallback(async (text) => {
        if (!text.trim()) return;

        const userMsg = { role: 'user', content: text, timestamp: new Date().toISOString() };
        setMessages(prev => [...prev, userMsg]);
        setLoading(true);

        // Add an empty assistant message to fill via streaming
        const streamId = Date.now();
        setMessages(prev => [...prev, {
            role: 'assistant', content: '', id: streamId,
            timestamp: new Date().toISOString(),
        }]);

        try {
            const res = await fetch(`${API}/chat/stream`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ text }),
            });
            const reader = res.body.getReader();
            const decoder = new TextDecoder();
            let accumulated = '';

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;
                const chunk = decoder.decode(value, { stream: true });
                const lines = chunk.split('\n');
                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        try {
                            const parsed = JSON.parse(line.slice(6));
                            if (parsed.token) {
                                accumulated += parsed.token;
                                setMessages(prev => prev.map(m =>
                                    m.id === streamId ? { ...m, content: accumulated } : m
                                ));
                            }
                        } catch { }
                    }
                }
            }
        } catch (err) {
            setMessages(prev => prev.map(m =>
                m.id === streamId ? { ...m, content: `⚠️ Stream error: ${err.message}` } : m
            ));
        } finally {
            setLoading(false);
        }
    }, []);

    // ── Upload file ────────────────────────────────────────────────────
    const uploadFile = useCallback(async (file) => {
        const formData = new FormData();
        formData.append('file', file);

        setMessages(prev => [...prev, {
            role: 'user', content: `📄 Uploaded: ${file.name}`,
            timestamp: new Date().toISOString(),
        }]);
        setLoading(true);

        try {
            const res = await fetch(`${API}/upload`, { method: 'POST', body: formData });
            const data = await res.json();
            setMessages(prev => [...prev, {
                role: 'assistant',
                content: data.message || `📄 Document '${data.filename}' uploaded and ready! You can now ask me anything about it.`,
                timestamp: new Date().toISOString(),
            }]);
        } catch (err) {
            setMessages(prev => [...prev, {
                role: 'assistant', content: `⚠️ Upload error: ${err.message}`,
                timestamp: new Date().toISOString(),
            }]);
        } finally {
            setLoading(false);
        }
    }, []);

    // ── Clear memory ───────────────────────────────────────────────────
    const clearMemory = useCallback(async () => {
        await fetch(`${API}/memory`, { method: 'DELETE' });
        setMemory([]);
        setMessages(prev => [...prev, {
            role: 'assistant', content: '🗑️ Memory cleared successfully.',
            timestamp: new Date().toISOString(),
        }]);
    }, []);

    // ── Quick actions ──────────────────────────────────────────────────
    const quickActions = [
        { icon: '📧', label: 'Check Emails', query: 'What emails do I have today?' },
        { icon: '📅', label: 'Check Calendar', query: 'What meetings do I have today?' },
        { icon: '🧠', label: 'What do you remember?', query: 'What do you remember about me?' },
    ];

    return (
        <div className="flex h-screen bg-[#0a0a0f]">
            {/* Left Sidebar */}
            <Sidebar
                memory={memory}
                onSelectQuery={sendMessage}
                activeView={activeView}
                onNavigate={setActiveView}
            />

            {/* Main Content Area */}
            {activeView === 'dashboard' ? (
                <EvalDashboard />
            ) : (
                <ChatWindow
                    messages={messages}
                    loading={loading}
                    onSend={sendMessage}
                    onStream={sendStream}
                    onUpload={uploadFile}
                />
            )}

            {/* Right Panel */}
            <RightPanel
                health={health}
                quickActions={quickActions}
                onQuickAction={sendMessage}
                onClearMemory={clearMemory}
            />
        </div>
    );
}

export default App;
