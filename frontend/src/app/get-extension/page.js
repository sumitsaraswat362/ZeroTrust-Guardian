'use client';

import { useState } from 'react';

export default function GetExtensionPage() {
  const [copied, setCopied] = useState(false);

  const steps = [
    {
      num: '1',
      title: 'Download the Extension',
      desc: 'The extension files are in the frontend-extension/ folder of this project.',
      icon: '📁',
    },
    {
      num: '2',
      title: 'Open Chrome Extensions',
      desc: null,
      icon: '🧩',
      action: (
        <button
          className="btn btn-primary"
          style={{ marginTop: '12px' }}
          onClick={() => {
            navigator.clipboard.writeText('chrome://extensions');
            setCopied(true);
            setTimeout(() => setCopied(false), 2000);
          }}
        >
          {copied ? '✓ Copied!' : 'Copy chrome://extensions'}
        </button>
      ),
      note: 'Paste this URL in your Chrome address bar and press Enter.',
    },
    {
      num: '3',
      title: 'Enable Developer Mode',
      desc: 'Toggle the "Developer mode" switch in the top-right corner of the extensions page.',
      icon: '🔧',
    },
    {
      num: '4',
      title: 'Load the Extension',
      desc: 'Click "Load unpacked" and select the frontend-extension/ folder from this project.',
      icon: '📦',
    },
    {
      num: '5',
      title: 'You\'re Protected!',
      desc: 'Browse to any website. The shield icon will appear showing your safety status in real time.',
      icon: '🛡️',
    },
  ];

  return (
    <div className="animate-in">
      <div className="page-header">
        <h2>Add to Chrome</h2>
        <p>Install ZeroTrust Guardian in 5 simple steps.</p>
      </div>

      <div style={{ maxWidth: '640px', margin: '0 auto', display: 'flex', flexDirection: 'column', gap: '20px' }}>
        {steps.map((step, i) => (
          <div
            key={i}
            className="glass-card"
            style={{
              display: 'flex', gap: '20px', alignItems: 'flex-start',
              animationDelay: `${i * 0.1}s`,
            }}
          >
            {/* Step number */}
            <div style={{
              width: '48px', height: '48px', borderRadius: '50%', flexShrink: 0,
              background: 'rgba(255,255,255,0.06)', display: 'flex',
              alignItems: 'center', justifyContent: 'center',
              fontSize: '20px', fontWeight: 700, color: 'var(--text-primary)',
            }}>
              {step.icon}
            </div>

            <div style={{ flex: 1 }}>
              <div style={{ fontSize: '11px', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: '4px' }}>
                Step {step.num}
              </div>
              <h3 style={{ fontSize: '20px', fontWeight: 600, marginBottom: '6px' }}>{step.title}</h3>
              {step.desc && (
                <p style={{ fontSize: '15px', color: 'var(--text-secondary)', lineHeight: 1.5 }}>
                  {step.desc}
                </p>
              )}
              {step.action}
              {step.note && (
                <p style={{ fontSize: '13px', color: 'var(--text-muted)', marginTop: '8px' }}>
                  {step.note}
                </p>
              )}
            </div>
          </div>
        ))}
      </div>

      {/* Requirements */}
      <div style={{ maxWidth: '640px', margin: '40px auto 0', textAlign: 'center' }}>
        <div style={{ fontSize: '13px', color: 'var(--text-muted)' }}>
          Requires Google Chrome · Backend must be running on localhost:8000
        </div>
      </div>
    </div>
  );
}
