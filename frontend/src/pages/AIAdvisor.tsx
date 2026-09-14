import React, { useState } from 'react';
import AdvisorChat from '../components/AdvisorChat';

export default function AIAdvisor() {
  const [activePrompt, setActivePrompt] = useState<string | undefined>();

  const promptSuggestions = [
    { icon: '🔴', text: 'Which asset needs immediate inspection?' },
    { icon: '🌩', text: 'How does current weather affect risk?' },
    { icon: '🏥', text: 'Which critical facilities are at risk?' },
    { icon: '👷', text: 'What should the maintenance team do today?' },
    { icon: '🔗', text: 'What happens if TX-001 fails?' },
    { icon: '📈', text: 'What is the cascade risk for this asset?' },
  ];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <div className="top-bar">
        <h2>🤖 AI Advisor</h2>
        <span className="text-muted text-sm" style={{ background: 'rgba(59,130,246,0.1)', padding: '2px 8px', borderRadius: '4px', border: '1px solid rgba(59,130,246,0.2)' }}>
          IBM Granite · watsonx.ai
        </span>
        <span className="text-muted text-sm" style={{ marginLeft: 'auto' }}>
          Powered by real-time grid data
        </span>
      </div>
      <div className="page-content" style={{ flex: 1, display: 'flex', gap: '24px', overflow: 'hidden' }}>
        {/* Chat panel */}
        <div className="glass-card" style={{ flex: 1, display: 'flex', flexDirection: 'column', padding: 0, overflow: 'hidden' }}>
          <div className="section-header" style={{ padding: '16px 20px', borderBottom: '1px solid var(--glass-border)', marginBottom: 0 }}>
            <span className="section-title">💬 AI Advisor Chat</span>
          </div>
          <AdvisorChat
            externalPrompt={activePrompt}
            onPromptProcessed={() => setActivePrompt(undefined)}
          />
        </div>

        {/* Info panel */}
        <div style={{ width: '300px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <div className="glass-card">
            <div className="section-header">
              <span className="section-title">Prompt Suggestions</span>
            </div>
            <div className="flex flex-col gap-2 text-sm text-secondary">
              {promptSuggestions.map((item, i) => (
                <button
                  key={i}
                  className="weather-alert-item text-left"
                  style={{
                    padding: '10px 12px',
                    background: 'rgba(15,23,42,0.6)',
                    border: '1px solid var(--glass-border)',
                    borderRadius: '8px',
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '10px',
                    width: '100%',
                    textAlign: 'left',
                    color: 'var(--text-primary)',
                    fontSize: '12px',
                    transition: 'all 0.2s ease',
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.borderColor = 'rgba(59,130,246,0.5)';
                    e.currentTarget.style.background = 'rgba(59,130,246,0.12)';
                    e.currentTarget.style.transform = 'translateX(3px)';
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.borderColor = 'var(--glass-border)';
                    e.currentTarget.style.background = 'rgba(15,23,42,0.6)';
                    e.currentTarget.style.transform = 'none';
                  }}
                  onClick={() => setActivePrompt(item.text)}
                  title="Click to ask AI Advisor"
                >
                  <span style={{ fontSize: '14px' }}>{item.icon}</span>
                  <span style={{ flex: 1 }}>{item.text}</span>
                </button>
              ))}
            </div>
          </div>

          <div className="glass-card">
            <div className="section-header">
              <span className="section-title">Model Specifications</span>
            </div>
            <div className="text-sm text-secondary" style={{ lineHeight: '1.8' }}>
              <div>Model: <span style={{ color: 'var(--blue-glow)' }}>IBM Granite 13B Instruct</span></div>
              <div>Platform: <span style={{ color: 'var(--blue-glow)' }}>watsonx.ai</span></div>
              <div>Fallback: <span style={{ color: 'var(--green)' }}>Local Rule Engine</span></div>
              <div className="text-muted text-sm mt-4">
                Always uses live grid data as context. Never uses hardcoded responses.
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

