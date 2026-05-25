/**
 * ChatWindow — Main chat interface with messages, input, voice recording, and file upload.
 *
 * Voice: MediaRecorder records audio → sends to /voice/transcribe (Whisper) → auto-sends message.
 * TTS: Auto-speaks every new AI response + click-to-listen on older messages.
 */

import { useState, useRef, useEffect, useCallback } from 'react';

const API = 'http://localhost:8000';

function ChatWindow({ messages, loading, onSend, onStream, onUpload }) {
    const [input, setInput] = useState('');
    const [isRecording, setIsRecording] = useState(false);
    const [useStreaming, setUseStreaming] = useState(false);
    const [autoSpeak, setAutoSpeak] = useState(true);
    const [isSpeaking, setIsSpeaking] = useState(false);
    const messagesEndRef = useRef(null);
    const fileInputRef = useRef(null);
    const mediaRecorderRef = useRef(null);
    const audioChunksRef = useRef([]);
    const prevMsgCountRef = useRef(0);

    // Auto-scroll to bottom on new messages
    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages, loading]);

    // Auto-speak new AI messages
    useEffect(() => {
        if (!autoSpeak || messages.length === 0) return;
        if (messages.length > prevMsgCountRef.current) {
            const lastMsg = messages[messages.length - 1];
            if (lastMsg.role === 'assistant' && lastMsg.content) {
                speakText(lastMsg.content.slice(0, 300));
            }
        }
        prevMsgCountRef.current = messages.length;
    }, [messages, autoSpeak]);

    const handleSend = () => {
        if (!input.trim()) return;
        if (useStreaming) {
            onStream(input);
        } else {
            onSend(input);
        }
        setInput('');
    };

    const handleKeyDown = (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSend();
        }
    };

    // ── Voice recording via MediaRecorder → Whisper ─────────────────────
    const toggleRecording = useCallback(async () => {
        if (isRecording) {
            // Stop recording
            if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
                mediaRecorderRef.current.stop();
            }
            setIsRecording(false);
            return;
        }

        // Start recording
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            const mediaRecorder = new MediaRecorder(stream, { mimeType: 'audio/webm' });
            audioChunksRef.current = [];

            mediaRecorder.ondataavailable = (event) => {
                if (event.data.size > 0) {
                    audioChunksRef.current.push(event.data);
                }
            };

            mediaRecorder.onstop = async () => {
                // Stop all tracks
                stream.getTracks().forEach(t => t.stop());

                const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });

                // Send to Whisper backend
                const formData = new FormData();
                formData.append('file', audioBlob, 'recording.webm');

                try {
                    setInput('🎤 Transcribing...');
                    const res = await fetch(`${API}/voice/transcribe`, {
                        method: 'POST',
                        body: formData,
                    });
                    const data = await res.json();

                    if (data.text && data.text.trim()) {
                        // Auto-send the transcribed text
                        setInput('');
                        onSend(data.text.trim());
                    } else {
                        setInput('');
                        alert('No speech detected. Please try again.');
                    }
                } catch (err) {
                    setInput('');
                    console.error('Transcription error:', err);
                    alert(`Transcription failed: ${err.message}`);
                }
            };

            mediaRecorderRef.current = mediaRecorder;
            mediaRecorder.start();
            setIsRecording(true);
        } catch (err) {
            console.error('Microphone error:', err);
            alert('Could not access microphone. Please allow microphone access.');
        }
    }, [isRecording, onSend]);

    // ── TTS: speak text aloud ───────────────────────────────────────────
    const speakText = (text) => {
        if (!window.speechSynthesis) return;
        window.speechSynthesis.cancel();
        // Clean markdown/emoji for cleaner speech
        const clean = text.replace(/[*#_`]/g, '').replace(/\bhttps?:\/\/\S+/g, 'link');
        const utterance = new SpeechSynthesisUtterance(clean);
        utterance.rate = 1.0;
        utterance.pitch = 1.0;
        utterance.lang = 'en-US';
        utterance.onstart = () => setIsSpeaking(true);
        utterance.onend = () => setIsSpeaking(false);
        utterance.onerror = () => setIsSpeaking(false);
        window.speechSynthesis.speak(utterance);
    };

    const stopSpeaking = () => {
        window.speechSynthesis.cancel();
        setIsSpeaking(false);
    };

    // ── File upload ─────────────────────────────────────────────────────
    const handleFileChange = (e) => {
        const file = e.target.files[0];
        if (file) onUpload(file);
        e.target.value = '';
    };

    // ── Tool badge extractor ────────────────────────────────────────────
    const getToolBadge = (msg) => {
        if (!msg.plan || msg.plan.length === 0) return null;
        const tools = msg.plan.map(s => s.tool).filter(t => t !== 'chat');
        if (tools.length === 0) return null;
        return tools.join(', ');
    };

    return (
        <div className="flex-1 flex flex-col min-w-0">
            {/* Header */}
            <div className="h-14 px-6 flex items-center justify-between border-b border-gray-800/60 bg-[#0d0d14]/80 backdrop-blur-sm shrink-0">
                <h2 className="text-sm font-semibold text-gray-300">Chat</h2>
                <div className="flex items-center gap-4">
                    <label className="flex items-center gap-2 text-xs text-gray-500 cursor-pointer select-none">
                        <input
                            type="checkbox"
                            checked={autoSpeak}
                            onChange={() => setAutoSpeak(!autoSpeak)}
                            className="rounded border-gray-600 bg-gray-800 text-blue-500 focus:ring-blue-500 focus:ring-offset-0 w-3.5 h-3.5"
                        />
                        🔊 Auto-speak
                    </label>
                    <label className="flex items-center gap-2 text-xs text-gray-500 cursor-pointer select-none">
                        <input
                            type="checkbox"
                            checked={useStreaming}
                            onChange={() => setUseStreaming(!useStreaming)}
                            className="rounded border-gray-600 bg-gray-800 text-blue-500 focus:ring-blue-500 focus:ring-offset-0 w-3.5 h-3.5"
                        />
                        Stream mode
                    </label>
                </div>
            </div>

            {/* Messages */}
            <div className="flex-1 overflow-y-auto px-6 py-5 space-y-4">
                {messages.length === 0 && (
                    <div className="flex flex-col items-center justify-center h-full text-center">
                        <div className="text-5xl mb-4">🤖</div>
                        <h2 className="text-xl font-bold text-gray-300 mb-2">Personal AI Agent</h2>
                        <p className="text-sm text-gray-500 max-w-md">
                            Ask me to check emails, manage your calendar, summarize documents, or just chat.
                        </p>
                        <div className="mt-6 flex gap-2 flex-wrap justify-center">
                            {['Summarize today\'s emails', 'What meetings do I have?', 'Hello!'].map(q => (
                                <button
                                    key={q}
                                    onClick={() => onSend(q)}
                                    className="px-3 py-1.5 text-xs rounded-full border border-gray-700 text-gray-400 hover:bg-gray-800 hover:text-gray-200 transition-colors"
                                >
                                    {q}
                                </button>
                            ))}
                        </div>
                    </div>
                )}

                {messages.map((msg, i) => (
                    <div
                        key={i}
                        className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'} animate-fade-in`}
                    >
                        <div className="max-w-[70%]">
                            {/* Bubble */}
                            <div
                                className={`px-4 py-3 rounded-2xl text-sm leading-relaxed whitespace-pre-wrap ${msg.role === 'user'
                                    ? 'bg-gradient-to-r from-blue-600 to-blue-500 text-white rounded-br-md'
                                    : 'bg-gray-800/80 text-gray-200 rounded-bl-md cursor-pointer hover:bg-gray-800 transition-colors'
                                    }`}
                                onClick={() => msg.role === 'assistant' && speakText(msg.content)}
                                title={msg.role === 'assistant' ? 'Click to read aloud 🔊' : ''}
                            >
                                {msg.content || <span className="text-gray-500 italic">Generating...</span>}
                            </div>

                            {/* Meta — tool used + score */}
                            {msg.role === 'assistant' && (msg.score || getToolBadge(msg)) && (
                                <div className="mt-1.5 px-1 flex items-center gap-3 text-[10px] text-gray-600">
                                    {getToolBadge(msg) && (
                                        <span>🔧 Used: <span className="text-gray-500">{getToolBadge(msg)}</span></span>
                                    )}
                                    {msg.score > 0 && (
                                        <span>⭐ Score: <span className="text-gray-500">{msg.score}/10</span></span>
                                    )}
                                    <span className="text-gray-700">🔊 click to listen</span>
                                </div>
                            )}
                        </div>
                    </div>
                ))}

                {/* Thinking indicator */}
                {loading && (
                    <div className="flex justify-start animate-fade-in">
                        <div className="px-5 py-3 rounded-2xl rounded-bl-md bg-gray-800/80">
                            <div className="flex items-center gap-2">
                                <span className="thinking-dot"></span>
                                <span className="thinking-dot"></span>
                                <span className="thinking-dot"></span>
                                <span className="text-xs text-gray-500 ml-2">Thinking...</span>
                            </div>
                        </div>
                    </div>
                )}

                <div ref={messagesEndRef} />
            </div>

            {/* Stop Speaking floating button */}
            {isSpeaking && (
                <button
                    onClick={stopSpeaking}
                    style={{
                        position: 'fixed',
                        bottom: '100px',
                        right: '30px',
                        background: '#ff4444',
                        color: 'white',
                        border: 'none',
                        borderRadius: '50px',
                        padding: '12px 24px',
                        cursor: 'pointer',
                        fontSize: '16px',
                        zIndex: 1000,
                        boxShadow: '0 4px 12px rgba(255,68,68,0.4)',
                        animation: 'fade-in 0.2s ease-out',
                    }}
                >
                    Stop Speaking
                </button>
            )}

            {/* Input Bar */}
            <div className="px-6 py-4 border-t border-gray-800/60 bg-[#0d0d14]/80 backdrop-blur-sm shrink-0">
                {/* Recording indicator */}
                {isRecording && (
                    <div className="flex items-center gap-2 mb-2 px-3 py-1.5 rounded-lg bg-red-500/10 border border-red-500/30">
                        <span className="w-2.5 h-2.5 rounded-full bg-red-500 animate-pulse" />
                        <span className="text-xs text-red-400 font-medium">Recording... Click 🎤 to stop and transcribe</span>
                    </div>
                )}

                <div className="flex items-center gap-2 max-w-4xl mx-auto">
                    {/* Voice button */}
                    <button
                        onClick={toggleRecording}
                        className={`p-2.5 rounded-xl transition-all shrink-0 ${isRecording
                            ? 'bg-red-500/20 text-red-400 ring-2 ring-red-500/50 animate-pulse'
                            : 'bg-gray-800 text-gray-500 hover:bg-gray-700 hover:text-gray-300'
                            }`}
                        title={isRecording ? 'Stop recording' : 'Voice input (Whisper)'}
                    >
                        🎤
                    </button>

                    {/* File upload button */}
                    <button
                        onClick={() => fileInputRef.current?.click()}
                        className="p-2.5 rounded-xl bg-gray-800 text-gray-500 hover:bg-gray-700 hover:text-gray-300 transition-colors shrink-0"
                        title="Upload PDF or DOCX"
                    >
                        📎
                    </button>
                    <input
                        ref={fileInputRef}
                        type="file"
                        accept=".pdf,.docx"
                        onChange={handleFileChange}
                        className="hidden"
                    />

                    {/* Text input */}
                    <input
                        type="text"
                        value={input}
                        onChange={e => setInput(e.target.value)}
                        onKeyDown={handleKeyDown}
                        placeholder={isRecording ? '🎤 Recording... speak now' : 'Ask me anything...'}
                        disabled={loading || isRecording}
                        className="flex-1 bg-gray-800/80 border border-gray-700/50 rounded-xl px-4 py-2.5 text-sm text-gray-200 placeholder-gray-600 focus:outline-none focus:ring-1 focus:ring-blue-500/50 focus:border-blue-500/50 disabled:opacity-50 transition-all"
                    />

                    {/* Send button */}
                    <button
                        onClick={handleSend}
                        disabled={loading || !input.trim() || isRecording}
                        className="px-4 py-2.5 rounded-xl bg-gradient-to-r from-blue-600 to-blue-500 text-white text-sm font-medium hover:from-blue-500 hover:to-blue-400 disabled:opacity-30 disabled:cursor-not-allowed transition-all shrink-0"
                    >
                        Send
                    </button>
                </div>
            </div>
        </div>
    );
}

export default ChatWindow;
