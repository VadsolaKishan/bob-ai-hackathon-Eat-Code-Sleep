import React, { useState, useRef, useEffect } from 'react';
import { sendChatMessage } from '../services/api';
import type { RiskLevel } from '../types';
import RiskBadge from './RiskBadge';

interface Message {
  role: 'user' | 'ai';
  text: string;
  provider?: string;
  timestamp: string;
  asset_id?: string;
  risk_level?: RiskLevel;
  risk_score?: number;
  recommended_actions?: string[];
  data_sources?: string[];
}

interface AdvisorChatProps {
  externalPrompt?: string;
  onPromptProcessed?: () => void;
}

export default function AdvisorChat({ externalPrompt, onPromptProcessed }: AdvisorChatProps = {}) {
  const [messages, setMessages] = useState<Message[]>([
    {
      role: 'ai',
      text: 'BOTTOM LINE:\nI am GridPulse AI, your intelligent power grid operational advisor.\n\nAsk me about asset health, IEEE C57.104 DGA fault classification, storm vulnerability, cascade failure graph analysis, or 48-hour crew pre-positioning plans.',
      provider: 'GridPulse AI Orchestrator',
      timestamp: new Date().toISOString(),
    }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  useEffect(() => {
    if (externalPrompt && externalPrompt.trim()) {
      send(externalPrompt.trim());
      onPromptProcessed?.();
    }
  }, [externalPrompt]);

  const send = async (textToSend?: string) => {
    const q = textToSend || input;
    if (!q.trim() || loading) return;

    const userMsg: Message = { role: 'user', text: q, timestamp: new Date().toISOString() };
    setMessages(prev => [...prev, userMsg]);
    setInput('');
    setLoading(true);

    try {
      const resp = await sendChatMessage(q);
      setMessages(prev => [...prev, {
        role: 'ai',
        text: resp.response,
        provider: resp.provider,
        timestamp: resp.timestamp,
        asset_id: resp.asset_id,
        risk_level: resp.risk_level,
        risk_score: resp.risk_score,
        recommended_actions: resp.recommended_actions,
        data_sources: resp.data_sources,
      }]);
    } catch (e) {
      setMessages(prev => [...prev, {
        role: 'ai',
        text: 'Unable to reach GridPulse AI backend. Please verify that the FastAPI API server is online.',
        provider: 'Error',
        timestamp: new Date().toISOString(),
      }]);
    } finally {
      setLoading(false);
    }
  };

  const handleKey = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send(); }
  };

  const suggestions = [
    'Which asset needs immediate inspection?',
    'How does current weather affect risk?',
    'Which critical facilities are at risk?',
    'What should the maintenance team do today?',
    'What happens if TX-001 fails?',
    'Why is TX-001 high risk?',
    'What does the DGA indicate for TX-001?',
    'Where should crews be positioned for the next 48 hours?',
    'Compare TX-001 and TX-004.',
    'Which assets are affected by lightning?',
  ];

  return (
    <div className="flex flex-col" style={{ flex: 1, height: '100%', overflow: 'hidden' }}>
      {/* Messages area */}
      <div style={{ flex: 1, overflowY: 'auto', padding: '20px', display: 'flex', flexDirection: 'column', gap: '18px' }}>
        {messages.map((msg, i) => (
          <div key={i} style={{ display: 'flex', justifyContent: msg.role === 'user' ? 'flex-end' : 'flex-start' }}>
            <div style={{
              maxWidth: '85%',
              padding: '14px 18px',
              borderRadius: msg.role === 'user' ? '16px 16px 4px 16px' : '16px 16px 16px 4px',
              background: msg.role === 'user'
                ? 'linear-gradient(135deg, rgba(37,99,235,0.3), rgba(29,78,216,0.15))'
                : 'var(--glass-bg)',
              border: '1px solid ' + (msg.role === 'user' ? 'rgba(59,130,246,0.4)' : 'var(--glass-border)'),
              fontSize: '13px',
              lineHeight: '1.6',
              boxShadow: msg.role === 'user' ? '0 4px 12px rgba(37,99,235,0.15)' : '0 4px 16px rgba(0,0,0,0.3)',
            }}>
              {/* Asset & Risk Meta Header if available */}
              {(msg.asset_id || msg.risk_level) && (
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '10px', paddingBottom: '8px', borderBottom: '1px solid var(--glass-border)' }}>
                  {msg.asset_id && (
                    <span style={{ fontWeight: 600, color: 'var(--blue-glow)', background: 'rgba(59,130,246,0.15)', padding: '2px 8px', borderRadius: '4px', fontSize: '12px' }}>
                      📍 {msg.asset_id}
                    </span>
                  )}
                  {msg.risk_level && (
                    <RiskBadge level={msg.risk_level} score={msg.risk_score} />
                  )}
                </div>
              )}

              {/* Message text with line break formatting */}
              <div style={{ whiteSpace: 'pre-line', color: 'var(--text-primary)' }}>
                {msg.text}
              </div>

              {/* Recommended actions checklist if available */}
              {msg.recommended_actions && msg.recommended_actions.length > 0 && (
                <div style={{ marginTop: '12px', padding: '10px 12px', background: 'rgba(15,23,42,0.6)', borderRadius: '8px', border: '1px solid var(--glass-border)' }}>
                  <div style={{ fontSize: '11px', fontWeight: 600, color: 'var(--blue-glow)', marginBottom: '6px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                    ⚡ Recommended Action Checklist
                  </div>
                  <ul style={{ margin: 0, paddingLeft: '16px', fontSize: '12px', color: 'var(--text-secondary)' }}>
                    {msg.recommended_actions.map((act, idx) => (
                      <li key={idx} style={{ marginBottom: '4px' }}>{act}</li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Data sources and Provider Footer */}
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '12px', marginTop: '10px', paddingTop: '8px', borderTop: '1px solid rgba(255,255,255,0.06)', fontSize: '11px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <span style={{
                    padding: '2px 6px',
                    borderRadius: '4px',
                    fontWeight: 600,
                    background: msg.provider === 'IBM Granite' ? 'rgba(59,130,246,0.2)' : 'rgba(148,163,184,0.15)',
                    color: msg.provider === 'IBM Granite' ? 'var(--blue-glow)' : 'var(--text-muted)',
                  }}>
                    {msg.provider === 'IBM Granite' ? '🤖 IBM Granite' : (msg.provider || 'Local Fallback')}
                  </span>
                  {msg.data_sources && msg.data_sources.length > 0 && (
                    <span style={{ color: 'var(--text-muted)' }}>
                      · Grounded in {msg.data_sources.slice(0, 2).join(', ')}
                    </span>
                  )}
                </div>
                <span style={{ color: 'var(--text-muted)' }}>
                  {new Date(msg.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                </span>
              </div>
            </div>
          </div>
        ))}

        {/* Loading state */}
        {loading && (
          <div className="loading-state text-muted text-sm" style={{ height: 'auto', padding: '8px', justifyContent: 'flex-start', gap: '10px' }}>
            <div className="spinner" />
            <span>GridPulse AI is analyzing live telemetry, DGA, weather, and grid graph...</span>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Quick suggestions */}
      <div style={{ padding: '8px 20px', display: 'flex', flexWrap: 'wrap', gap: '8px', borderTop: '1px solid rgba(99,179,237,0.08)' }}>
        {suggestions.map((s, i) => (
          <button key={i} className="btn btn-ghost text-sm" style={{ padding: '4px 10px', fontSize: '11px' }}
            onClick={() => send(s)}>
            {s}
          </button>
        ))}
      </div>

      {/* Pinned Input bar */}
      <div style={{ padding: '16px 20px', borderTop: '1px solid var(--glass-border)', display: 'flex', gap: '12px', background: 'rgba(10,14,26,0.5)' }}>
        <input
          className="input"
          style={{ flex: 1 }}
          placeholder="Ask in plain English (e.g. 'Why is TX-001 high risk?', 'What happens if TX-001 fails?')..."
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={handleKey}
          disabled={loading}
        />
        <button className="btn btn-primary" onClick={() => send()} disabled={loading || !input.trim()}>
          Ask Advisor 🚀
        </button>
      </div>
    </div>
  );
}
