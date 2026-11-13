'use client';

import { useState, useRef, useEffect } from 'react';
import { api } from '@/lib/api';
import { cn } from '@/lib/utils';

const ANALYSIS_TYPES = [
  { id: 'business_snapshot', label: 'Business', icon: '🏢' },
  { id: 'financial_snapshot', label: 'Financials', icon: '📊' },
  { id: 'trajectory', label: 'Trajectory', icon: '📈' },
  { id: 'balance_sheet', label: 'Balance Sheet', icon: '🏦' },
  { id: 'cash_quality', label: 'Cash Quality', icon: '💰' },
  { id: 'narrative_vs_numbers', label: 'Narrative vs Numbers', icon: '🎭' },
  { id: 'guidance', label: 'Guidance', icon: '🔮' },
  { id: 'bull_bear', label: 'Bull vs Bear', icon: '⚔️' },
];

interface Message {
  role: 'user' | 'finn';
  content: string;
  type?: string;
  timestamp: Date;
}

export function PullView() {
  const [messages, setMessages] = useState<Message[]>([
    {
      role: 'finn',
      content: "I'm FINN. Ask me to research any NSE-listed company — pick an analysis type below, or just ask a question.\n\nI ground everything in primary filings. No broker notes, no news noise.",
      timestamp: new Date(),
    },
  ]);
  const [input, setInput] = useState('');
  const [selectedTicker, setSelectedTicker] = useState('');
  const [loading, setLoading] = useState(false);
  const [mode, setMode] = useState<'chat' | 'structured'>('chat');
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: 'smooth' });
  }, [messages]);

  async function handleChat(e?: React.FormEvent) {
    e?.preventDefault();
    if (!input.trim() || loading) return;

    const userMsg: Message = { role: 'user', content: input, timestamp: new Date() };
    setMessages(prev => [...prev, userMsg]);
    setInput('');
    setLoading(true);

    try {
      const res = await api.chat(input);
      setMessages(prev => [...prev, {
        role: 'finn',
        content: res.response,
        timestamp: new Date(),
      }]);
    } catch (err) {
      setMessages(prev => [...prev, {
        role: 'finn',
        content: 'Connection error. Is the backend running?',
        timestamp: new Date(),
      }]);
    } finally {
      setLoading(false);
    }
  }

  async function handleStructuredAnalysis(analysisType: string) {
    if (!selectedTicker || loading) return;

    const label = ANALYSIS_TYPES.find(t => t.id === analysisType)?.label || analysisType;
    const userMsg: Message = {
      role: 'user',
      content: `Run ${label} analysis on ${selectedTicker}`,
      type: analysisType,
      timestamp: new Date(),
    };
    setMessages(prev => [...prev, userMsg]);
    setLoading(true);

    try {
      const res = await api.researchCompany(selectedTicker, analysisType);
      setMessages(prev => [...prev, {
        role: 'finn',
        content: res.content,
        type: analysisType,
        timestamp: new Date(),
      }]);
    } catch (err) {
      setMessages(prev => [...prev, {
        role: 'finn',
        content: 'Analysis failed. Check if the ticker is valid and the backend is running.',
        timestamp: new Date(),
      }]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex flex-col h-full -mx-4 -mt-3">
      {/* Mode toggle */}
      <div className="flex gap-1 px-4 py-2 bg-finn-surface/50">
        <button
          onClick={() => setMode('chat')}
          className={cn(
            'px-3 py-1.5 text-xs rounded-lg transition-all',
            mode === 'chat' ? 'bg-finn-accent/20 text-finn-accent font-medium' : 'text-finn-muted'
          )}
        >
          💬 Chat
        </button>
        <button
          onClick={() => setMode('structured')}
          className={cn(
            'px-3 py-1.5 text-xs rounded-lg transition-all',
            mode === 'structured' ? 'bg-finn-accent/20 text-finn-accent font-medium' : 'text-finn-muted'
          )}
        >
          📋 Structured
        </button>
      </div>

      {/* Structured mode — ticker + quick picks + analysis type selector */}
      {mode === 'structured' && (
        <div className="px-4 py-3 border-b border-finn-border bg-finn-surface/30">
          <div className="flex gap-2 mb-2">
            <input
              type="text"
              value={selectedTicker}
              onChange={(e) => setSelectedTicker(e.target.value.toUpperCase())}
              placeholder="Enter ticker (e.g. TCS.NS or RELIANCE.NS)"
              className="flex-1 bg-finn-card border border-finn-border rounded-lg px-3 py-2 text-xs text-white placeholder-finn-muted focus:outline-none focus:border-finn-accent font-mono"
            />
            {selectedTicker && (
              <button
                onClick={() => setSelectedTicker('')}
                className="px-2 py-1 text-xxs text-finn-muted hover:text-white"
              >
                Clear
              </button>
            )}
          </div>

          {/* Quick Ticker Pills */}
          <div className="flex items-center gap-1.5 overflow-x-auto pb-2.5 pt-0.5 no-scrollbar">
            <span className="text-xxs text-finn-muted shrink-0">Picks:</span>
            {['TCS.NS', 'RELIANCE.NS', 'INFY.NS', 'HDFCBANK.NS', 'TATAMOTORS.NS', 'ZOMATO.NS', 'TRENT.NS'].map(t => (
              <button
                key={t}
                onClick={() => setSelectedTicker(t)}
                className={cn(
                  'px-2 py-0.5 rounded text-xxs font-mono shrink-0 transition-all border',
                  selectedTicker === t
                    ? 'bg-finn-accent/20 border-finn-accent text-finn-accent font-bold'
                    : 'bg-finn-card border-finn-border text-finn-text-dim hover:border-finn-muted'
                )}
              >
                {t.replace('.NS', '')}
              </button>
            ))}
          </div>

          <div className="grid grid-cols-2 gap-1.5">
            {ANALYSIS_TYPES.map((type) => (
              <button
                key={type.id}
                onClick={() => handleStructuredAnalysis(type.id)}
                disabled={!selectedTicker || loading}
                className={cn(
                  "flex items-center gap-2 px-3 py-2 bg-finn-card border border-finn-border rounded-lg text-xs text-finn-text hover:border-finn-accent/40 transition-all disabled:opacity-40 disabled:cursor-not-allowed",
                  type.id === 'narrative_vs_numbers' && 'border-indigo-500/40 bg-indigo-950/20'
                )}
              >
                <span>{type.icon}</span>
                <span className="truncate">{type.label}</span>
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Suggested Chat Questions when chat is empty or starting */}
      {mode === 'chat' && messages.length <= 1 && (
        <div className="px-4 py-2 border-b border-finn-border/50 bg-finn-surface/30">
          <p className="text-xxs text-finn-muted mb-1.5">Suggested analyst queries:</p>
          <div className="space-y-1">
            {[
              "Compare TCS actual margins vs management guidance over last 4 quarters",
              "What are Tata Motors JLR margin and demerger updates?",
              "Assess HDFC Bank balance-sheet leverage and ROCE trend",
              "Is Reliance cash flow keeping pace with capital expenditure?"
            ].map(q => (
              <button
                key={q}
                onClick={() => {
                  setInput(q);
                }}
                className="w-full text-left text-xxs text-finn-text-dim hover:text-white bg-finn-card/60 p-1.5 rounded border border-finn-border/40 truncate block transition-all"
              >
                💡 {q}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Messages */}
      <div ref={scrollRef} className="flex-1 overflow-y-auto px-4 py-3 space-y-3">
        {messages.map((msg, i) => (
          <div
            key={i}
            className={cn(
              'animate-slide-up',
              msg.role === 'user' ? 'flex justify-end' : 'flex justify-start'
            )}
          >
            <div className={cn(
              'max-w-[85%] rounded-2xl px-4 py-3',
              msg.role === 'user'
                ? 'bg-finn-accent text-white rounded-br-sm'
                : 'bg-finn-card border border-finn-border rounded-bl-sm'
            )}>
              <p className="text-sm leading-relaxed whitespace-pre-line">{msg.content}</p>
              <span className="text-xxs opacity-50 mt-1 block">
                {msg.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
              </span>
            </div>
          </div>
        ))}
        {loading && (
          <div className="flex justify-start">
            <div className="bg-finn-card border border-finn-border rounded-2xl rounded-bl-sm px-4 py-3">
              <div className="flex items-center gap-1.5">
                <div className="w-1.5 h-1.5 rounded-full bg-finn-accent animate-bounce" style={{ animationDelay: '0ms' }} />
                <div className="w-1.5 h-1.5 rounded-full bg-finn-accent animate-bounce" style={{ animationDelay: '150ms' }} />
                <div className="w-1.5 h-1.5 rounded-full bg-finn-accent animate-bounce" style={{ animationDelay: '300ms' }} />
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Chat input */}
      {mode === 'chat' && (
        <form onSubmit={handleChat} className="px-4 py-3 border-t border-finn-border bg-finn-surface/50">
          <div className="flex gap-2">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask FINN about any company..."
              className="flex-1 bg-finn-card border border-finn-border rounded-xl px-4 py-2.5 text-sm text-white placeholder-finn-muted focus:outline-none focus:border-finn-accent"
              disabled={loading}
            />
            <button
              type="submit"
              disabled={!input.trim() || loading}
              className="px-4 py-2.5 bg-finn-accent rounded-xl text-white text-sm font-medium disabled:opacity-40 transition-all hover:bg-finn-accent-dim"
            >
              ↑
            </button>
          </div>
        </form>
      )}
    </div>
  );
}
