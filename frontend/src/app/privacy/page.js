'use client';

import Link from 'next/link';

export default function PrivacyPage() {
  const principles = [
    {
      icon: '💻',
      title: 'Local Analysis',
      desc: 'All scanning happens on YOUR machine. Zero data sent to any cloud.',
      accent: 'var(--low)',
    },
    {
      icon: '🚫',
      title: 'No Tracking',
      desc: "We don't collect, store, or sell any browsing data. Ever.",
      accent: 'var(--info)',
    },
    {
      icon: '📖',
      title: 'Open Source',
      desc: 'Every line of code is auditable on GitHub. Trust through transparency.',
      accent: 'var(--accent)',
    },
  ];

  const flowSteps = [
    { icon: '🌐', label: 'Your Browser' },
    { icon: '🧩', label: 'Extension' },
    { icon: '🖥️', label: 'Local Backend', sub: 'localhost' },
    { icon: '🤖', label: 'AI Analysis' },
    { icon: '✅', label: 'Result Displayed' },
  ];

  const comparisons = [
    { feature: 'Data Collection', zt: 'None', ztIcon: '🟢', other: 'Everything', otherIcon: '🔴' },
    { feature: 'Processing', zt: 'Local', ztIcon: '🟢', other: 'Cloud', otherIcon: '🔴' },
    { feature: 'Tracking', zt: 'Zero', ztIcon: '🟢', other: 'Extensive', otherIcon: '🔴' },
    { feature: 'Source Code', zt: 'Open', ztIcon: '🟢', other: 'Closed', otherIcon: '🔴' },
    { feature: 'Cost', zt: 'Free', ztIcon: '🟢', other: '$$$', otherIcon: '🔴' },
  ];

  return (
    <div>
      {/* ── Hero ─────────────────────────────────────────────────────── */}
      <section className="hero-section" style={{ paddingBottom: '40px' }}>
        <div
          className="animate-in"
          style={{
            fontSize: '96px',
            lineHeight: 1,
            marginBottom: '24px',
            filter: 'drop-shadow(0 0 40px rgba(50,215,75,0.3))',
          }}
        >
          🔒
        </div>
        <h1 className="hero-title animate-in animate-in-delay-1">
          Privacy First.{' '}
          <span className="gradient-text">Always.</span>
        </h1>
        <p className="hero-subtitle animate-in animate-in-delay-2">
          Your data never leaves your device.
        </p>
      </section>

      {/* ── Privacy Principles ───────────────────────────────────────── */}
      <section style={{ padding: '40px 0 80px' }}>
        <h2 className="section-title">Our Privacy Principles</h2>
        <p className="section-subtitle">
          Not just promises — architectural guarantees.
        </p>

        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
            gap: '24px',
          }}
        >
          {principles.map((p, i) => (
            <div
              key={i}
              className={`glass-card animate-in animate-in-delay-${i + 1}`}
              style={{
                position: 'relative',
                overflow: 'hidden',
                textAlign: 'center',
                padding: '48px 32px',
              }}
            >
              {/* Subtle glow at top */}
              <div
                style={{
                  position: 'absolute',
                  top: 0,
                  left: '50%',
                  transform: 'translateX(-50%)',
                  width: '120px',
                  height: '2px',
                  background: `linear-gradient(90deg, transparent, ${p.accent}, transparent)`,
                  borderRadius: '2px',
                }}
              />
              <div style={{ fontSize: '48px', marginBottom: '20px' }}>
                {p.icon}
              </div>
              <h3
                style={{
                  fontSize: '22px',
                  fontWeight: 600,
                  marginBottom: '12px',
                  color: 'var(--text-primary)',
                }}
              >
                {p.title}
              </h3>
              <p
                style={{
                  fontSize: '15px',
                  color: 'var(--text-secondary)',
                  lineHeight: 1.6,
                }}
              >
                {p.desc}
              </p>
            </div>
          ))}
        </div>
      </section>

      {/* ── How It Works — Architecture ──────────────────────────────── */}
      <section style={{ padding: '40px 0 80px' }}>
        <h2 className="section-title">How It Works</h2>
        <p className="section-subtitle">
          Data stays on your machine at every step.
        </p>

        {/* Architecture Diagram */}
        <div
          className="glass-card animate-in"
          style={{
            padding: '48px 32px',
            position: 'relative',
            overflow: 'hidden',
          }}
        >
          {/* "Never leaves your device" banner */}
          <div
            style={{
              position: 'absolute',
              top: '16px',
              right: '20px',
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              padding: '6px 14px',
              borderRadius: 'var(--radius-full)',
              background: 'rgba(50,215,75,0.1)',
              border: '1px solid rgba(50,215,75,0.2)',
            }}
          >
            <span
              style={{
                width: '6px',
                height: '6px',
                borderRadius: '50%',
                background: 'var(--low)',
                boxShadow: '0 0 8px var(--low)',
              }}
            />
            <span
              style={{
                fontSize: '11px',
                fontWeight: 600,
                color: 'var(--low)',
                textTransform: 'uppercase',
                letterSpacing: '0.06em',
              }}
            >
              100% Local
            </span>
          </div>

          {/* Flow diagram */}
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '0',
              flexWrap: 'wrap',
              padding: '24px 0 16px',
            }}
          >
            {flowSteps.map((step, i) => (
              <div
                key={i}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                }}
              >
                {/* Step box */}
                <div
                  style={{
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                    gap: '10px',
                    padding: '24px 20px',
                    minWidth: '120px',
                    background: 'rgba(255,255,255,0.04)',
                    border: '1px solid rgba(255,255,255,0.08)',
                    borderRadius: 'var(--radius-md)',
                    transition: 'all var(--fast)',
                  }}
                >
                  <span style={{ fontSize: '32px' }}>{step.icon}</span>
                  <span
                    style={{
                      fontSize: '13px',
                      fontWeight: 600,
                      color: 'var(--text-primary)',
                      textAlign: 'center',
                      lineHeight: 1.3,
                    }}
                  >
                    {step.label}
                  </span>
                  {step.sub && (
                    <span
                      style={{
                        fontSize: '11px',
                        color: 'var(--low)',
                        fontWeight: 500,
                        fontFamily: 'monospace',
                        background: 'rgba(50,215,75,0.1)',
                        padding: '2px 8px',
                        borderRadius: 'var(--radius-sm)',
                      }}
                    >
                      {step.sub}
                    </span>
                  )}
                </div>

                {/* Arrow connector */}
                {i < flowSteps.length - 1 && (
                  <div
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      padding: '0 6px',
                      color: 'var(--text-muted)',
                      fontSize: '20px',
                      fontWeight: 300,
                      userSelect: 'none',
                    }}
                  >
                    →
                  </div>
                )}
              </div>
            ))}
          </div>

          {/* Security boundary line */}
          <div
            style={{
              marginTop: '24px',
              padding: '16px 0',
              borderTop: '1px dashed rgba(50,215,75,0.2)',
              textAlign: 'center',
            }}
          >
            <span
              style={{
                fontSize: '13px',
                color: 'var(--text-muted)',
                fontWeight: 500,
              }}
            >
              🔒 Everything above runs entirely on{' '}
              <span style={{ color: 'var(--low)' }}>your device</span>
              . No external servers. No cloud calls. No exceptions.
            </span>
          </div>
        </div>
      </section>

      {/* ── Comparison Table ─────────────────────────────────────────── */}
      <section style={{ padding: '40px 0 80px' }}>
        <h2 className="section-title">ZeroTrust vs Others</h2>
        <p className="section-subtitle">
          See the difference a privacy-first architecture makes.
        </p>

        <div
          className="glass-card animate-in"
          style={{ padding: '0', overflow: 'hidden' }}
        >
          {/* Table header */}
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: '1fr 1fr 1fr',
              padding: '20px 32px',
              borderBottom: '1px solid var(--glass-border)',
              background: 'rgba(255,255,255,0.02)',
            }}
          >
            <span
              style={{
                fontSize: '12px',
                fontWeight: 600,
                color: 'var(--text-muted)',
                textTransform: 'uppercase',
                letterSpacing: '0.08em',
              }}
            >
              Feature
            </span>
            <span
              style={{
                fontSize: '12px',
                fontWeight: 600,
                color: 'var(--low)',
                textTransform: 'uppercase',
                letterSpacing: '0.08em',
                textAlign: 'center',
              }}
            >
              ZeroTrust Guardian
            </span>
            <span
              style={{
                fontSize: '12px',
                fontWeight: 600,
                color: 'var(--text-muted)',
                textTransform: 'uppercase',
                letterSpacing: '0.08em',
                textAlign: 'center',
              }}
            >
              Others
            </span>
          </div>

          {/* Table rows */}
          {comparisons.map((row, i) => (
            <div
              key={i}
              style={{
                display: 'grid',
                gridTemplateColumns: '1fr 1fr 1fr',
                padding: '18px 32px',
                borderBottom:
                  i < comparisons.length - 1
                    ? '1px solid rgba(255,255,255,0.04)'
                    : 'none',
                transition: 'background var(--fast)',
              }}
              onMouseEnter={(e) =>
                (e.currentTarget.style.background = 'rgba(255,255,255,0.03)')
              }
              onMouseLeave={(e) =>
                (e.currentTarget.style.background = 'transparent')
              }
            >
              <span
                style={{
                  fontSize: '15px',
                  fontWeight: 500,
                  color: 'var(--text-primary)',
                  display: 'flex',
                  alignItems: 'center',
                }}
              >
                {row.feature}
              </span>

              {/* ZeroTrust value */}
              <span
                style={{
                  fontSize: '15px',
                  fontWeight: 600,
                  color: 'var(--low)',
                  textAlign: 'center',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '8px',
                }}
              >
                {row.ztIcon} {row.zt}
              </span>

              {/* Others value */}
              <span
                style={{
                  fontSize: '15px',
                  fontWeight: 500,
                  color: 'var(--critical)',
                  textAlign: 'center',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '8px',
                  opacity: 0.8,
                }}
              >
                {row.otherIcon} {row.other}
              </span>
            </div>
          ))}
        </div>
      </section>

      {/* ── CTA ──────────────────────────────────────────────────────── */}
      <section className="cta-section">
        <div className="glass-card cta-card">
          <div style={{ fontSize: '48px', marginBottom: '20px' }}>🛡️</div>
          <h3
            style={{
              fontSize: '40px',
              fontWeight: 700,
              letterSpacing: '-0.02em',
              marginBottom: '12px',
            }}
          >
            Your privacy is{' '}
            <span className="gradient-text">non-negotiable.</span>
          </h3>
          <p
            style={{
              fontSize: '20px',
              color: 'var(--text-secondary)',
              marginBottom: '32px',
              maxWidth: '560px',
              margin: '0 auto 32px',
            }}
          >
            Verify every claim. Audit the code. Run it yourself.
          </p>
          <div
            style={{
              display: 'flex',
              gap: '12px',
              justifyContent: 'center',
              flexWrap: 'wrap',
            }}
          >
            <a
              href="https://github.com/sumitsaraswat362/ZeroTrust-Guardian"
              target="_blank"
              rel="noopener noreferrer"
              className="btn btn-primary"
              style={{ padding: '16px 40px', fontSize: '17px' }}
            >
              View on GitHub
            </a>
            <Link
              href="/get-extension"
              className="btn btn-secondary"
              style={{ padding: '16px 40px', fontSize: '17px' }}
            >
              Add to Chrome — Free
            </Link>
          </div>
        </div>
      </section>

      {/* ── Footer ───────────────────────────────────────────────────── */}
      <div
        style={{
          textAlign: 'center',
          padding: '24px 0 60px',
          color: 'var(--text-muted)',
          fontSize: '13px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          gap: '16px',
          flexWrap: 'wrap',
        }}
      >
        <span>100% Local Processing</span>
        <span>•</span>
        <span>Zero Data Collection</span>
        <span>•</span>
        <span>Open Source</span>
        <span>•</span>
        <a
          href="https://github.com/sumitsaraswat362/ZeroTrust-Guardian"
          target="_blank"
          rel="noopener noreferrer"
          style={{ color: 'var(--text-muted)' }}
        >
          GitHub ↗
        </a>
      </div>
    </div>
  );
}
