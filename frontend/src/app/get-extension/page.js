'use client';

import { useState } from 'react';

const EXTENSION_ZIP_URL = 'https://github.com/sumitsaraswat362/ZeroTrust-Guardian/archive/refs/heads/main.zip';
const REPO_URL = 'https://github.com/sumitsaraswat362/ZeroTrust-Guardian';

export default function GetExtensionPage() {
  const [copied, setCopied] = useState(false);
  const [activeStep, setActiveStep] = useState(0);

  const handleCopy = () => {
    navigator.clipboard.writeText('chrome://extensions');
    setCopied(true);
    setTimeout(() => setCopied(false), 2500);
  };

  const steps = [
    {
      num: '1',
      title: 'Download Extension Files',
      icon: '⬇️',
      content: (
        <div>
          <p style={{ fontSize: '15px', color: 'var(--text-secondary)', lineHeight: 1.6, marginBottom: '16px' }}>
            Click the button below to download the project. After downloading, unzip it and locate the <strong style={{ color: 'var(--text-primary)' }}>frontend-extension</strong> folder inside.
          </p>
          <a
            href={EXTENSION_ZIP_URL}
            className="btn btn-primary"
            style={{ display: 'inline-flex', alignItems: 'center', gap: '8px' }}
            download
          >
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
              <path d="M8 1v10M8 11L4 7M8 11l4-4M2 14h12" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
            Download ZeroTrust Guardian
          </a>
          <p style={{ fontSize: '13px', color: 'var(--text-muted)', marginTop: '10px' }}>
            ~2 MB · Contains extension + backend + documentation
          </p>
        </div>
      ),
    },
    {
      num: '2',
      title: 'Open Chrome Extensions Page',
      icon: '🧩',
      content: (
        <div>
          <p style={{ fontSize: '15px', color: 'var(--text-secondary)', lineHeight: 1.6, marginBottom: '16px' }}>
            Open Google Chrome, then paste this address into your address bar and press Enter.
          </p>
          <div style={{
            display: 'flex', alignItems: 'center', gap: '12px',
            background: 'rgba(255,255,255,0.04)', borderRadius: 'var(--radius-sm)',
            padding: '12px 16px', marginBottom: '12px', border: '1px solid var(--glass-border)',
          }}>
            <code style={{ flex: 1, fontSize: '15px', color: 'var(--text-primary)', fontFamily: 'monospace' }}>
              chrome://extensions
            </code>
            <button
              className="btn btn-primary"
              style={{ padding: '6px 16px', fontSize: '13px', flexShrink: 0 }}
              onClick={handleCopy}
            >
              {copied ? '✓ Copied!' : 'Copy'}
            </button>
          </div>
        </div>
      ),
    },
    {
      num: '3',
      title: 'Enable Developer Mode',
      icon: '🔧',
      content: (
        <div>
          <p style={{ fontSize: '15px', color: 'var(--text-secondary)', lineHeight: 1.6 }}>
            On the Extensions page, find the <strong style={{ color: 'var(--text-primary)' }}>Developer mode</strong> toggle in the <strong style={{ color: 'var(--text-primary)' }}>top-right corner</strong> of the page and turn it on.
          </p>
          <div style={{
            marginTop: '16px', padding: '14px 20px',
            background: 'rgba(100,210,255,0.06)', borderRadius: 'var(--radius-sm)',
            border: '1px solid rgba(100,210,255,0.1)', fontSize: '14px', color: 'var(--info)',
          }}>
            💡 This is required for all Chrome extensions that aren&apos;t on the Chrome Web Store.
          </div>
        </div>
      ),
    },
    {
      num: '4',
      title: 'Load the Extension',
      icon: '📦',
      content: (
        <div>
          <p style={{ fontSize: '15px', color: 'var(--text-secondary)', lineHeight: 1.6 }}>
            Click the <strong style={{ color: 'var(--text-primary)' }}>&quot;Load unpacked&quot;</strong> button that appeared at the top-left. In the file picker, navigate to the downloaded folder and select the <strong style={{ color: 'var(--text-primary)' }}>frontend-extension</strong> folder.
          </p>
        </div>
      ),
    },
    {
      num: '5',
      title: 'You\'re Protected! 🎉',
      icon: '🛡️',
      content: (
        <div>
          <p style={{ fontSize: '15px', color: 'var(--text-secondary)', lineHeight: 1.6, marginBottom: '16px' }}>
            That&apos;s it! Browse to any website. The ZeroTrust shield icon will appear in your toolbar, showing you the safety status of every page you visit in real time.
          </p>
          <div style={{
            padding: '14px 20px',
            background: 'rgba(50,215,75,0.06)', borderRadius: 'var(--radius-sm)',
            border: '1px solid rgba(50,215,75,0.1)', fontSize: '14px', color: 'var(--low)',
          }}>
            ✅ Pin the extension to your toolbar for quick access: click the puzzle piece icon → pin ZeroTrust Guardian.
          </div>
        </div>
      ),
    },
  ];

  return (
    <div className="animate-in">
      <div className="page-header" style={{ textAlign: 'center' }}>
        <div style={{ fontSize: '56px', marginBottom: '12px' }}>🛡️</div>
        <h2 style={{ fontSize: '40px', fontWeight: 700, letterSpacing: '-0.03em' }}>Add to Chrome</h2>
        <p style={{ fontSize: '20px', color: 'var(--text-secondary)', maxWidth: '440px', margin: '8px auto 0' }}>
          Install ZeroTrust Guardian in under 2 minutes.
        </p>
      </div>

      <div style={{ maxWidth: '640px', margin: '0 auto', display: 'flex', flexDirection: 'column', gap: '16px' }}>
        {steps.map((step, i) => (
          <div
            key={i}
            className="glass-card"
            style={{
              padding: '28px 28px',
              cursor: 'pointer',
              border: activeStep === i ? '1px solid var(--accent)' : '1px solid var(--glass-border)',
              transition: 'all var(--spring)',
            }}
            onClick={() => setActiveStep(activeStep === i ? -1 : i)}
          >
            <div style={{ display: 'flex', gap: '16px', alignItems: 'center' }}>
              {/* Step number circle */}
              <div style={{
                width: '44px', height: '44px', borderRadius: '50%', flexShrink: 0,
                background: activeStep === i ? 'var(--accent)' : 'rgba(255,255,255,0.06)',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                fontSize: '18px', fontWeight: 700, color: activeStep === i ? '#fff' : 'var(--text-secondary)',
                transition: 'all var(--spring)',
              }}>
                {step.num}
              </div>

              <div style={{ flex: 1 }}>
                <div style={{ fontSize: '11px', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.08em' }}>
                  Step {step.num} of {steps.length}
                </div>
                <h3 style={{ fontSize: '18px', fontWeight: 600, marginTop: '2px' }}>{step.title}</h3>
              </div>

              <div style={{
                fontSize: '20px',
                transform: activeStep === i ? 'rotate(180deg)' : 'rotate(0deg)',
                transition: 'transform var(--spring)',
                color: 'var(--text-muted)',
              }}>
                ▾
              </div>
            </div>

            {/* Expandable content */}
            <div style={{
              maxHeight: activeStep === i ? '400px' : '0',
              overflow: 'hidden',
              transition: 'max-height 0.4s cubic-bezier(0.16, 1, 0.3, 1)',
              marginTop: activeStep === i ? '20px' : '0',
              paddingLeft: '60px',
            }}>
              {step.content}
            </div>
          </div>
        ))}
      </div>

      {/* Quick links */}
      <div style={{ maxWidth: '640px', margin: '40px auto 0', textAlign: 'center' }}>
        <div style={{ display: 'flex', gap: '24px', justifyContent: 'center', flexWrap: 'wrap', fontSize: '14px' }}>
          <a href={REPO_URL} target="_blank" rel="noopener noreferrer" style={{ color: 'var(--text-secondary)' }}>
            ⭐ Star on GitHub
          </a>
          <a href={`${REPO_URL}/issues`} target="_blank" rel="noopener noreferrer" style={{ color: 'var(--text-secondary)' }}>
            🐛 Report a Bug
          </a>
          <a href={`${REPO_URL}#readme`} target="_blank" rel="noopener noreferrer" style={{ color: 'var(--text-secondary)' }}>
            📖 Documentation
          </a>
        </div>
        <div style={{ fontSize: '13px', color: 'var(--text-muted)', marginTop: '16px' }}>
          Requires Google Chrome · Free &amp; open source
        </div>
      </div>
    </div>
  );
}
