'use client';

import { useState } from 'react';
import Link from 'next/link';

export default function CheckLinkPage() {
  const [url, setUrl] = useState('');
  const [result, setResult] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [backendOffline, setBackendOffline] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!url.trim()) return;
    setIsLoading(true);
    setResult(null);
    setError('');
    setBackendOffline(false);

    try {
      const res = await fetch('http://localhost:8000/api/v1/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url: url.trim() }),
        signal: AbortSignal.timeout(15000),
      });
      if (!res.ok) throw new Error(`Server error (${res.status})`);
      setResult(await res.json());
    } catch (err) {
      if (err.name === 'TimeoutError' || err.message === 'Failed to fetch' || err.name === 'TypeError') {
        setBackendOffline(true);
      } else {
        setError(err.message || 'Could not reach analysis engine.');
      }
    } finally {
      setIsLoading(false);
    }
  };

  const statusMap = {
    safe: { icon: '🛡️', label: 'Verified Safe', color: '#32d74b' },
    warning: { icon: '⚠️', label: 'Caution Advised', color: '#ff9500' },
    danger: { icon: '🛑', label: 'Threat Detected', color: '#ff3b30' },
    scam: { icon: '🛑', label: 'Scam Detected', color: '#ff3b30' },
    unknown: { icon: '❓', label: 'Unknown', color: '#86868b' },
  };

  const getStatus = (s) => statusMap[s] || statusMap.unknown;

  const exampleUrls = [
    { label: 'google.com', url: 'https://google.com' },
    { label: 'github.com', url: 'https://github.com' },
    { label: 'suspicious IP link', url: 'http://192.168.1.1/login/verify-account/paypal' },
  ];

  return (
    <div className="animate-in">
      <div className="page-header">
        <h2>Check a Link</h2>
        <p>Paste any URL to instantly see if it&apos;s safe to visit.</p>
      </div>

      <form onSubmit={handleSubmit}>
        <div className="scan-input-container">
          <div className="scan-input-wrapper">
            <input
              className="input"
              type="text"
              placeholder="https://example.com"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              disabled={isLoading}
            />
            <button className="btn btn-primary" type="submit" disabled={isLoading}>
              {isLoading ? <><span className="spinner" /> Analyzing...</> : 'Analyze'}
            </button>
          </div>
        </div>
      </form>

      {/* Examples */}
      {!result && !isLoading && !error && !backendOffline && (
        <div style={{ textAlign: 'center', marginTop: '32px' }}>
          <div style={{ fontSize: '13px', color: 'var(--text-muted)', marginBottom: '12px', textTransform: 'uppercase', letterSpacing: '0.08em', fontWeight: 600 }}>
            Try an example
          </div>
          <div style={{ display: 'flex', gap: '10px', justifyContent: 'center', flexWrap: 'wrap' }}>
            {exampleUrls.map((ex) => (
              <button
                key={ex.url}
                className="btn btn-secondary"
                style={{ fontSize: '14px', padding: '8px 18px' }}
                onClick={() => setUrl(ex.url)}
              >
                {ex.label}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Backend Offline — Friendly guidance */}
      {backendOffline && (
        <div className="glass-card animate-in" style={{ marginTop: '32px', textAlign: 'center', padding: '48px 32px' }}>
          <div style={{ fontSize: '56px', marginBottom: '16px' }}>🔌</div>
          <h3 style={{ fontSize: '24px', fontWeight: 700, marginBottom: '12px' }}>Analysis Engine Not Running</h3>
          <p style={{ fontSize: '17px', color: 'var(--text-secondary)', maxWidth: '440px', margin: '0 auto', lineHeight: 1.6, marginBottom: '24px' }}>
            The AI analysis engine runs locally on your machine for maximum privacy. 
            Start it to scan links.
          </p>
          <div style={{
            background: 'rgba(255,255,255,0.04)', borderRadius: 'var(--radius-md)',
            padding: '20px', maxWidth: '400px', margin: '0 auto 20px', textAlign: 'left',
          }}>
            <div style={{ fontSize: '11px', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: '12px' }}>
              Quick Start
            </div>
            <code style={{ display: 'block', fontSize: '14px', color: 'var(--info)', lineHeight: 1.8, fontFamily: 'monospace' }}>
              cd backend<br/>
              pip install -r requirements.txt<br/>
              uvicorn main:app --reload
            </code>
          </div>
          <p style={{ fontSize: '14px', color: 'var(--text-muted)' }}>
            Or install the <Link href="/get-extension" style={{ color: 'var(--accent)' }}>Chrome Extension</Link> for automatic protection.
          </p>
        </div>
      )}

      {/* Error */}
      {error && (
        <div className="glass-card" style={{ marginTop: '32px', borderLeft: '4px solid #ff3b30' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <span style={{ fontSize: '24px' }}>❌</span>
            <div>
              <div style={{ fontWeight: 600, fontSize: '17px', marginBottom: '4px' }}>Analysis Failed</div>
              <div style={{ fontSize: '15px', color: 'var(--text-secondary)' }}>{error}</div>
            </div>
          </div>
        </div>
      )}

      {/* Result */}
      {result && (() => {
        const s = getStatus(result.status);
        const circumference = 2 * Math.PI * 54;
        const offset = circumference * (1 - (result.trust_score || 0) / 100);
        let hostname = '';
        try { hostname = new URL(result.url).hostname; } catch { hostname = result.url; }

        return (
          <div className="animate-in" style={{ marginTop: '48px' }}>
            {/* Main Result Card */}
            <div className="glass-card" style={{ padding: '48px', textAlign: 'center' }}>
              {/* Score Ring */}
              <div style={{ position: 'relative', width: '160px', height: '160px', margin: '0 auto 24px' }}>
                <svg width="160" height="160" viewBox="0 0 160 160">
                  <circle cx="80" cy="80" r="54" fill="none" stroke="rgba(255,255,255,0.06)" strokeWidth="10" />
                  <circle
                    cx="80" cy="80" r="54" fill="none"
                    stroke={s.color} strokeWidth="10" strokeLinecap="round"
                    strokeDasharray={circumference}
                    strokeDashoffset={offset}
                    transform="rotate(-90 80 80)"
                    style={{ transition: 'stroke-dashoffset 1.5s cubic-bezier(0.16, 1, 0.3, 1)' }}
                  />
                </svg>
                <div style={{ position: 'absolute', inset: 0, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center' }}>
                  <span style={{ fontSize: '48px', fontWeight: 700, letterSpacing: '-0.04em', lineHeight: 1 }}>
                    {result.trust_score ?? '--'}
                  </span>
                </div>
              </div>

              <div style={{ fontSize: '14px', color: 'var(--text-muted)', marginBottom: '8px', textTransform: 'uppercase', letterSpacing: '0.08em', fontWeight: 600 }}>Trust Score</div>

              <div style={{ display: 'flex', alignItems: 'center', gap: '10px', justifyContent: 'center', marginBottom: '12px' }}>
                <span style={{ fontSize: '28px' }}>{s.icon}</span>
                <span style={{ fontSize: '28px', fontWeight: 700, color: s.color, letterSpacing: '-0.02em' }}>
                  {s.label}
                </span>
              </div>

              <p style={{ fontSize: '17px', color: 'var(--text-secondary)', maxWidth: '500px', margin: '0 auto', lineHeight: 1.5 }}>
                {result.reason}
              </p>
              <div style={{ fontSize: '13px', color: 'var(--text-muted)', marginTop: '12px' }}>
                {hostname}
              </div>
            </div>

            {/* Threats */}
            {result.threats?.length > 0 && (
              <div style={{ marginTop: '32px' }}>
                <h3 style={{ fontSize: '22px', fontWeight: 600, marginBottom: '20px' }}>
                  Detected Issues ({result.threats.length})
                </h3>
                {result.threats.map((t, i) => (
                  <div key={i} className="vuln-card">
                    <div className="vuln-card-header">
                      <div className="vuln-card-title">{t.title}</div>
                      <span className={`severity-badge ${t.severity}`}>{t.severity}</span>
                    </div>
                    <div className="vuln-card-desc">{t.description}</div>
                  </div>
                ))}
              </div>
            )}

            {/* No Threats */}
            {result.threats?.length === 0 && (
              <div style={{ textAlign: 'center', padding: '60px 20px', color: 'var(--text-muted)' }}>
                <div style={{ fontSize: '48px', marginBottom: '12px' }}>✅</div>
                <div style={{ fontSize: '20px', fontWeight: 600, color: 'var(--text-secondary)' }}>No Issues Found</div>
                <p style={{ fontSize: '15px', marginTop: '8px' }}>This website passed all safety checks.</p>
              </div>
            )}

            {/* AI Analysis */}
            {result.details?.ai_analysis && (
              <div className="glass-card" style={{ marginTop: '24px', borderLeft: '4px solid var(--info)' }}>
                <div style={{ fontSize: '11px', fontWeight: 600, color: 'var(--info)', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: '8px' }}>
                  AI Analysis
                </div>
                <p style={{ fontSize: '17px', color: 'var(--text-secondary)', lineHeight: 1.6 }}>
                  {result.details.ai_analysis}
                </p>
              </div>
            )}
          </div>
        );
      })()}
    </div>
  );
}
