"use client";

// Direct backend URL — bypasses Next.js rewrite buffering for SSE streams
const BACKEND = "http://localhost:8000";

import { useState, useRef, useEffect, useCallback } from "react";
import {
  Send,
  Mic,
  MicOff,
  ShoppingBag,
  LayoutDashboard,
  Bot,
  User,
  Loader2,
  CheckCircle,
  XCircle,
  Volume2,
} from "lucide-react";
import Link from "next/link";

interface Message {
  role: "user" | "assistant";
  content: string;
  timestamp: Date;
}

interface ReasoningEntry {
  type: string;
  content?: string;
  tool?: string;
  input?: Record<string, unknown>;
  output?: Record<string, unknown>;
}

// ── Voice hook: Web Speech API (STT) + OpenAI TTS ─────────────────────────
// Flow: mic button → Web Speech API transcribes → sends to LangGraph agent
//       → agent text reply → POST /api/tts → OpenAI TTS plays audio back
function useVoice(onTranscript: (text: string) => void) {
  const [isVoiceMode, setIsVoiceMode] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [transcript, setTranscript] = useState("");
  const [voiceError, setVoiceError] = useState<string | null>(null);

  const recognitionRef = useRef<unknown>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  const stopSpeaking = useCallback(() => {
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current.currentTime = 0;
      audioRef.current = null;
    }
    setIsSpeaking(false);
  }, []);

  // Called by ChatPage after agent finishes streaming a reply
  const speak = useCallback(async (text: string) => {
    if (!text.trim() || !isVoiceMode) return;
    stopSpeaking();
    try {
      setIsSpeaking(true);
      const res = await fetch(`${BACKEND}/api/tts`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: text.slice(0, 4000), voice: "alloy" }),
      });
      if (!res.ok) throw new Error(`TTS error ${res.status}`);
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const audio = new Audio(url);
      audioRef.current = audio;
      audio.onended = () => { setIsSpeaking(false); URL.revokeObjectURL(url); };
      audio.onerror = () => { setIsSpeaking(false); URL.revokeObjectURL(url); };
      await audio.play();
    } catch (err) {
      console.error("TTS error:", err);
      setIsSpeaking(false);
    }
  }, [isVoiceMode, stopSpeaking]);

  const startListening = useCallback(() => {
    if (typeof window === "undefined" || !("webkitSpeechRecognition" in window)) {
      setVoiceError("Speech recognition not supported — use Chrome or Edge.");
      return;
    }
    stopSpeaking();
    setVoiceError(null);

    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const SR = (window as any).webkitSpeechRecognition;
    const rec = new SR();
    recognitionRef.current = rec;
    rec.continuous = false;
    rec.interimResults = true;
    rec.lang = "en-US";

    rec.onresult = (e: {
      results: { [i: number]: { [j: number]: { transcript: string }; isFinal: boolean } };
      resultIndex: number;
    }) => {
      let interim = "";
      let final = "";
      for (let i = e.resultIndex; i < Object.keys(e.results).length; i++) {
        const t = e.results[i][0].transcript;
        e.results[i].isFinal ? (final += t) : (interim += t);
      }
      setTranscript(final || interim);
      if (final) {
        setIsListening(false);
        setTranscript("");
        onTranscript(final.trim());
      }
    };
    rec.onerror = (e: { error: string }) => {
      setVoiceError(`Mic error: ${e.error}`);
      setIsListening(false);
    };
    rec.onend = () => setIsListening(false);
    rec.start();
    setIsListening(true);
  }, [onTranscript, stopSpeaking]);

  const stopListening = useCallback(() => {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    (recognitionRef.current as any)?.stop();
    setIsListening(false);
    setTranscript("");
  }, []);

  const toggleVoice = useCallback(() => {
    if (isVoiceMode) {
      stopListening();
      stopSpeaking();
      setIsVoiceMode(false);
      setVoiceError(null);
    } else {
      setIsVoiceMode(true);
    }
  }, [isVoiceMode, stopListening, stopSpeaking]);

  return {
    isVoiceMode, isListening, isSpeaking, transcript, voiceError,
    toggleVoice, startListening, stopListening, speak, stopSpeaking,
  };
}

const WELCOME_MSG: Message = {
  role: "assistant",
  content: "Hello! I'm ShopEase's AI support agent. I can help you with refund requests. Please share your customer ID or email and describe your issue.",
  timestamp: new Date(),
};

function saveMessages(msgs: Message[]) {
  try { sessionStorage.setItem("chat_messages", JSON.stringify(msgs)); } catch { /* ignore */ }
}

// ── Main chat page ─────────────────────────────────────────────────────────
export default function ChatPage() {
  // Start with welcome message — sessionStorage is loaded in useEffect after hydration
  const [messages, setMessages] = useState<Message[]>([WELCOME_MSG]);
  const [input, setInput] = useState("");
  const [isStreaming, setIsStreaming] = useState(false);
  // Simple random UUID — no sessionStorage access at init time (SSR-safe)
  const [sessionId, setSessionId] = useState<string>(() => crypto.randomUUID());
  const [reasoning, setReasoning] = useState<ReasoningEntry[]>([]);
  const [showReasoning, setShowReasoning] = useState(false);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const abortRef = useRef<AbortController | null>(null);

  // sendMessage is defined below — forward ref so useVoice can call it
  const sendMessageRef = useRef<(text: string) => void>(() => {});

  const {
    isVoiceMode, isListening, isSpeaking, transcript, voiceError,
    toggleVoice, startListening, stopListening, speak, stopSpeaking,
  } = useVoice((text) => sendMessageRef.current(text));

  // Restore messages from sessionStorage after hydration (client-only, SSR-safe)
  useEffect(() => {
    try {
      const raw = sessionStorage.getItem("chat_messages");
      if (raw) {
        const parsed = JSON.parse(raw) as Array<{ role: string; content: string; timestamp: string }>;
        const loaded = parsed.map((m) => ({
          ...m,
          role: m.role as "user" | "assistant",
          timestamp: new Date(m.timestamp),
        }));
        if (loaded.length > 0) setMessages(loaded);
      }
    } catch { /* ignore corrupt data */ }
  }, []); // runs once after mount

  // Persist messages to sessionStorage on every update
  useEffect(() => { saveMessages(messages); }, [messages]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Auto-resize textarea
  useEffect(() => {
    if (inputRef.current) {
      inputRef.current.style.height = "auto";
      inputRef.current.style.height = `${inputRef.current.scrollHeight}px`;
    }
  }, [input]);

  const sendMessage = useCallback(
    async (text: string) => {
      if (!text.trim() || isStreaming) return;

      const userMsg: Message = { role: "user", content: text.trim(), timestamp: new Date() };
      setMessages((prev) => [...prev, userMsg]);
      setInput("");
      setIsStreaming(true);

      const assistantPlaceholder: Message = { role: "assistant", content: "", timestamp: new Date() };
      setMessages((prev) => [...prev, assistantPlaceholder]);

      let accumulated = "";

      try {
        abortRef.current = new AbortController();
        const res = await fetch(`${BACKEND}/api/chat`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ message: text.trim(), session_id: sessionId }),
          signal: abortRef.current.signal,
        });

        const sid = res.headers.get("X-Session-ID");
        if (sid) setSessionId(sid);

        const reader = res.body!.getReader();
        const decoder = new TextDecoder();

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          const chunk = decoder.decode(value, { stream: true });
          for (const line of chunk.split("\n")) {
            if (!line.startsWith("data: ")) continue;
            const raw = line.slice(6).trim();
            if (!raw) continue;
            try {
              const event = JSON.parse(raw);
              if (event.type === "token") {
                accumulated += event.content;
                setMessages((prev) => {
                  const updated = [...prev];
                  updated[updated.length - 1] = { ...updated[updated.length - 1], content: accumulated };
                  return updated;
                });
              } else if (event.type === "reasoning") {
                setReasoning((prev) => [...prev, { type: "reasoning", content: event.content }]);
              }
            } catch { /* ignore */ }
          }
        }
      } catch (err: unknown) {
        if (err instanceof Error && err.name !== "AbortError") {
          accumulated = "Sorry, I encountered an error. Please check that the backend is running.";
          setMessages((prev) => {
            const updated = [...prev];
            updated[updated.length - 1] = { ...updated[updated.length - 1], content: accumulated };
            return updated;
          });
        }
      } finally {
        setIsStreaming(false);
        // In voice mode, speak the agent reply after streaming completes
        if (accumulated) speak(accumulated);
      }
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [isStreaming, sessionId, speak]
  );

  // Keep the ref in sync so useVoice's onTranscript always calls the latest sendMessage
  useEffect(() => { sendMessageRef.current = sendMessage; }, [sendMessage]);

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage(input);
    }
  };

  const getDecisionBadge = (content: string) => {
    if (content.includes("APPROVED") || content.toLowerCase().includes("approved"))
      return (
        <span className="inline-flex items-center gap-1 text-xs font-semibold text-green-700 bg-green-100 px-2 py-0.5 rounded-full">
          <CheckCircle className="w-3 h-3" /> Approved
        </span>
      );
    if (content.includes("DENIED") || content.toLowerCase().includes("denied"))
      return (
        <span className="inline-flex items-center gap-1 text-xs font-semibold text-red-700 bg-red-100 px-2 py-0.5 rounded-full">
          <XCircle className="w-3 h-3" /> Denied
        </span>
      );
    return null;
  };

  return (
    <div className="flex flex-col h-screen bg-slate-50">
      {/* Header */}
      <header className="bg-white border-b border-slate-200 px-6 py-4 flex items-center justify-between shadow-sm">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 bg-sky-600 rounded-xl flex items-center justify-center">
            <ShoppingBag className="w-5 h-5 text-white" />
          </div>
          <div>
            <h1 className="font-semibold text-slate-900 text-lg leading-tight">
              ShopEase Support
            </h1>
            <p className="text-xs text-slate-500">AI Refund Agent • Powered by GPT-4o</p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={() => setShowReasoning((s) => !s)}
            className="text-sm text-slate-600 hover:text-sky-600 transition-colors flex items-center gap-1.5"
          >
            <Bot className="w-4 h-4" />
            {showReasoning ? "Hide" : "Show"} reasoning
          </button>
          <Link
            href="/admin"
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-1.5 text-sm bg-slate-100 hover:bg-slate-200 text-slate-700 px-3 py-1.5 rounded-lg transition-colors"
          >
            <LayoutDashboard className="w-4 h-4" />
            Admin
          </Link>
        </div>
      </header>

      <div className="flex flex-1 overflow-hidden">
        {/* Chat area */}
        <main className="flex-1 flex flex-col overflow-hidden">
          {/* Messages */}
          <div className="flex-1 overflow-y-auto px-4 py-6 space-y-4">
            {messages.map((msg, i) => (
              <div
                key={i}
                className={`flex gap-3 ${msg.role === "user" ? "flex-row-reverse" : "flex-row"}`}
              >
                {/* Avatar */}
                <div
                  className={`w-8 h-8 rounded-full flex-shrink-0 flex items-center justify-center ${
                    msg.role === "user"
                      ? "bg-sky-600"
                      : "bg-slate-700"
                  }`}
                >
                  {msg.role === "user" ? (
                    <User className="w-4 h-4 text-white" />
                  ) : (
                    <Bot className="w-4 h-4 text-white" />
                  )}
                </div>

                {/* Bubble */}
                <div
                  className={`max-w-[75%] rounded-2xl px-4 py-3 shadow-sm ${
                    msg.role === "user"
                      ? "bg-sky-600 text-white rounded-tr-sm"
                      : "bg-white text-slate-800 rounded-tl-sm border border-slate-100"
                  }`}
                >
                  {msg.role === "assistant" && msg.content === "" && isStreaming ? (
                    <div className="flex gap-1 items-center py-1">
                      <span className="typing-dot w-2 h-2 rounded-full bg-slate-400 inline-block" />
                      <span className="typing-dot w-2 h-2 rounded-full bg-slate-400 inline-block" />
                      <span className="typing-dot w-2 h-2 rounded-full bg-slate-400 inline-block" />
                    </div>
                  ) : (
                    <>
                      <p className="text-sm leading-relaxed whitespace-pre-wrap">
                        {msg.content}
                      </p>
                      {msg.role === "assistant" && (
                        <div className="mt-1.5">
                          {getDecisionBadge(msg.content)}
                        </div>
                      )}
                    </>
                  )}
                  <p
                    className={`text-[10px] mt-1 ${
                      msg.role === "user" ? "text-sky-200" : "text-slate-400"
                    }`}
                  >
                    {msg.timestamp.toLocaleTimeString([], {
                      hour: "2-digit",
                      minute: "2-digit",
                    })}
                  </p>
                </div>
              </div>
            ))}
            <div ref={messagesEndRef} />
          </div>

          {/* Voice error banner */}
          {voiceError && (
            <div className="mx-4 mb-2 bg-red-50 border border-red-200 rounded-xl px-4 py-2 flex items-center gap-2">
              <XCircle className="w-4 h-4 text-red-500 flex-shrink-0" />
              <span className="text-sm text-red-700">{voiceError}</span>
            </div>
          )}

          {/* Voice active banner */}
          {isVoiceMode && !voiceError && (
            <div className={`mx-4 mb-2 rounded-xl px-4 py-2 flex items-center gap-2 border transition-colors ${
              isSpeaking ? "bg-violet-50 border-violet-200"
              : isListening ? "bg-red-50 border-red-200"
              : "bg-slate-50 border-slate-200"
            }`}>
              <div className="relative flex-shrink-0">
                <div className={`w-3 h-3 rounded-full ${isSpeaking ? "bg-violet-500" : isListening ? "bg-red-500" : "bg-sky-500"}`} />
                {(isListening || isSpeaking) && (
                  <div className={`absolute inset-0 rounded-full animate-ping opacity-75 ${isSpeaking ? "bg-violet-400" : "bg-red-400"}`} />
                )}
              </div>
              <span className={`text-sm font-medium ${isSpeaking ? "text-violet-700" : isListening ? "text-red-700" : "text-slate-600"}`}>
                {isSpeaking ? "Agent speaking…" : isListening ? "Listening — speak now" : "Voice mode on — press mic to speak"}
              </span>
              {transcript && (
                <span className="text-xs text-slate-500 ml-auto italic truncate max-w-[220px]">
                  &ldquo;{transcript}&rdquo;
                </span>
              )}
              {isSpeaking && (
                <button onClick={stopSpeaking} className="ml-auto text-xs text-violet-600 hover:underline">
                  Stop
                </button>
              )}
            </div>
          )}

          {/* Input area */}
          <div className="border-t border-slate-200 bg-white px-4 py-4">
            <div className="flex items-end gap-3 max-w-3xl mx-auto">
              {/* Voice button
                  - Single click when voice mode OFF → enable voice mode
                  - Single click when voice mode ON  → start listening (push-to-talk)
                  - Right-click / long-press         → disable voice mode         */}
              <button
                onClick={isVoiceMode ? (isListening ? stopListening : startListening) : toggleVoice}
                onContextMenu={(e) => { e.preventDefault(); if (isVoiceMode) toggleVoice(); }}
                title={
                  isVoiceMode
                    ? isListening ? "Stop listening" : "Tap to speak (right-click to exit voice mode)"
                    : "Enable voice mode (Web Speech API + OpenAI TTS)"
                }
                className={`relative flex-shrink-0 w-11 h-11 rounded-full flex items-center justify-center transition-all ${
                  isSpeaking ? "bg-violet-500 hover:bg-violet-600 text-white"
                  : isListening ? "bg-red-500 hover:bg-red-600 text-white mic-pulse"
                  : isVoiceMode ? "bg-sky-600 hover:bg-sky-700 text-white"
                  : "bg-slate-100 hover:bg-slate-200 text-slate-600"
                }`}
              >
                {isSpeaking ? <Volume2 className="w-5 h-5" /> : isListening ? <MicOff className="w-5 h-5" /> : <Mic className="w-5 h-5" />}
              </button>

              {/* Text input */}
              <div className="flex-1 relative">
                <textarea
                  ref={inputRef}
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={handleKeyDown}
                  placeholder="Describe your issue or paste your order ID…"
                  rows={1}
                  className="w-full resize-none rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 pr-12 text-sm text-slate-800 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-sky-500 focus:border-transparent transition-all max-h-32 overflow-y-auto"
                  disabled={isStreaming}
                />
              </div>

              {/* Send button */}
              <button
                onClick={() => sendMessage(input)}
                disabled={!input.trim() || isStreaming}
                className="flex-shrink-0 w-11 h-11 rounded-full bg-sky-600 hover:bg-sky-700 disabled:bg-slate-200 text-white flex items-center justify-center transition-all"
              >
                {isStreaming ? (
                  <Loader2 className="w-5 h-5 animate-spin" />
                ) : (
                  <Send className="w-5 h-5" />
                )}
              </button>
            </div>
            <p className="text-center text-xs text-slate-400 mt-2">
              Session: <span className="font-mono">{sessionId.slice(0, 8)}…</span>
            </p>
          </div>
        </main>

        {/* Reasoning panel */}
        {showReasoning && (
          <aside className="w-80 border-l border-slate-200 bg-white flex flex-col overflow-hidden">
            <div className="px-4 py-3 border-b border-slate-100 flex items-center justify-between">
              <h2 className="text-sm font-semibold text-slate-700 flex items-center gap-2">
                <Bot className="w-4 h-4 text-sky-600" />
                Agent Reasoning
              </h2>
              <span className="text-xs bg-sky-100 text-sky-700 px-2 py-0.5 rounded-full font-medium">
                {reasoning.length} steps
              </span>
            </div>
            <div className="flex-1 overflow-y-auto p-3 space-y-2">
              {reasoning.length === 0 ? (
                <p className="text-xs text-slate-400 text-center py-8">
                  Reasoning steps will appear here as the agent works…
                </p>
              ) : (
                reasoning.map((entry, i) => (
                  <div
                    key={i}
                    className="log-entry text-xs bg-slate-50 rounded-lg p-2.5 border border-slate-100"
                  >
                    <span className="text-slate-500">{entry.content}</span>
                  </div>
                ))
              )}
            </div>
          </aside>
        )}
      </div>
    </div>
  );
}
