import React from 'react';
import AdvisorChat from '../components/AdvisorChat';

export default function AIAdvisor() {
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
          <AdvisorChat />
        </div>

        {/* Info panel */}
        <div style={{ width: '300px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <div className="glass-card">
            <div className="section-header">
              <span className="section-title">Prompt Suggestions</span>
            </div>
            <div className="flex flex-col gap-2 text-sm text-secondary">
              {[
                '🔴 Which asset needs immediate inspection?',
                '🌩 How does current weather affect risk?',
                '🏥 Which critical facilities are at risk?',
                '👷 What should the maintenance team do today?',
                '🔗 What happens if TX-001 fails?',
                '📈 What is the cascade risk for this asset?',
              ].map((q, i) => (
                <div key={i} className="weather-alert-item" style={{ padding: '8px', background: 'rgba(15,23,42,0.5)', border: '1px solid var(--glass-border)' }}>{q}</div>
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

