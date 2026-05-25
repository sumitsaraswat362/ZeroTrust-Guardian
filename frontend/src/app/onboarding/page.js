'use client';

import { useState, useCallback } from 'react';
import Link from 'next/link';

/* ─── Slide Data ─────────────────────────────────────────────────────────── */
const slides = [
  {
    icon: '🛡️',
    title: 'Welcome to ZeroTrust Guardian',
    subtitle: 'Your AI-powered shield against online threats.',
    pulse: true,
  },
  {
    icon: '🤖',
    title: 'Invisible Protection',
    features: [
      { icon: '🔍', label: 'Scans every page' },
      { icon: '🧠', label: 'AI analyzes threats' },
      { icon: '⚡', label: 'Alerts you instantly' },
    ],
  },
  {
    icon: '🔒',
    title: 'Your Privacy is Sacred',
    body: 'All analysis runs locally on your device. We never see, store, or sell your browsing data.',
  },
  {
    icon: '✨',
    title: "You're All Set",
    final: true,
  },
];

/* ─── Component ──────────────────────────────────────────────────────────── */
export default function OnboardingPage() {
  const [current, setCurrent] = useState(0);

  const next = useCallback(() => {
    setCurrent((prev) => Math.min(prev + 1, slides.length - 1));
  }, []);

  return (
    <div style={styles.wrapper}>
      {/* ── Slide Track ─────────────────────────────────────────────────── */}
      <div
        style={{
          ...styles.track,
          transform: `translateX(-${current * 100}vw)`,
        }}
      >
        {slides.map((slide, i) => (
          <div key={i} style={styles.slide}>
            <div
              style={{
                ...styles.slideInner,
                opacity: current === i ? 1 : 0,
                transform: current === i ? 'scale(1) translateY(0)' : 'scale(0.92) translateY(24px)',
                transition: 'opacity 0.6s cubic-bezier(0.16,1,0.3,1), transform 0.6s cubic-bezier(0.16,1,0.3,1)',
              }}
            >
              {/* Icon */}
              <div
                style={{
                  ...styles.iconWrap,
                  animation: slide.pulse ? 'onb-pulse 2.4s ease-in-out infinite' : 'none',
                }}
              >
                <span style={styles.icon}>{slide.icon}</span>
              </div>

              {/* Title */}
              <h1 className="gradient-text" style={styles.title}>
                {slide.title}
              </h1>

              {/* Subtitle (slide 0) */}
              {slide.subtitle && (
                <p style={styles.subtitle}>{slide.subtitle}</p>
              )}

              {/* Body text (slide 2) */}
              {slide.body && (
                <p style={styles.body}>{slide.body}</p>
              )}

              {/* Feature mini-cards (slide 1) */}
              {slide.features && (
                <div style={styles.featureRow}>
                  {slide.features.map((f, fi) => (
                    <div key={fi} className="glass-card" style={styles.featureCard}>
                      <span style={styles.featureIcon}>{f.icon}</span>
                      <span style={styles.featureLabel}>{f.label}</span>
                    </div>
                  ))}
                </div>
              )}

              {/* Actions */}
              <div style={styles.actions}>
                {i === 0 && (
                  <button className="btn btn-primary" onClick={next} style={styles.actionBtn}>
                    Get Started
                  </button>
                )}

                {(i === 1 || i === 2) && (
                  <button className="btn btn-primary" onClick={next} style={styles.actionBtn}>
                    Next
                  </button>
                )}

                {slide.final && (
                  <div style={styles.finalActions}>
                    <Link href="/scan" className="btn btn-primary" style={styles.actionBtn}>
                      Check a Link
                    </Link>
                    <Link href="/get-extension" className="btn btn-secondary" style={styles.actionBtn}>
                      Add to Chrome
                    </Link>
                  </div>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* ── Progress Dots ───────────────────────────────────────────────── */}
      <div style={styles.dots}>
        {slides.map((_, i) => (
          <button
            key={i}
            onClick={() => setCurrent(i)}
            aria-label={`Go to slide ${i + 1}`}
            style={{
              ...styles.dot,
              ...(current === i ? styles.dotActive : {}),
            }}
          />
        ))}
      </div>

      {/* ── Keyframe injection ──────────────────────────────────────────── */}
      <style>{`
        @keyframes onb-pulse {
          0%, 100% { transform: scale(1); }
          50% { transform: scale(1.08); }
        }
      `}</style>
    </div>
  );
}

/* ─── Styles ─────────────────────────────────────────────────────────────── */
const styles = {
  wrapper: {
    position: 'fixed',
    inset: 0,
    zIndex: 50,
    overflow: 'hidden',
  },
  track: {
    display: 'flex',
    height: '100%',
    transition: 'transform 0.7s cubic-bezier(0.16, 1, 0.3, 1)',
    willChange: 'transform',
  },
  slide: {
    minWidth: '100vw',
    height: '100vh',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    padding: '40px 24px',
  },
  slideInner: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    textAlign: 'center',
    maxWidth: 620,
    width: '100%',
  },
  iconWrap: {
    width: 96,
    height: 96,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: '50%',
    background: 'rgba(255,255,255,0.05)',
    border: '1px solid rgba(255,255,255,0.08)',
    marginBottom: 32,
  },
  icon: {
    fontSize: 48,
    lineHeight: 1,
  },
  title: {
    fontSize: 'clamp(32px, 6vw, 48px)',
    fontWeight: 700,
    letterSpacing: '-0.03em',
    lineHeight: 1.1,
    marginBottom: 16,
  },
  subtitle: {
    fontSize: 20,
    fontWeight: 500,
    color: 'var(--text-secondary)',
    lineHeight: 1.4,
    maxWidth: 460,
    marginBottom: 48,
  },
  body: {
    fontSize: 18,
    fontWeight: 400,
    color: 'var(--text-secondary)',
    lineHeight: 1.6,
    maxWidth: 480,
    marginBottom: 48,
  },
  featureRow: {
    display: 'flex',
    gap: 16,
    marginTop: 12,
    marginBottom: 48,
    flexWrap: 'wrap',
    justifyContent: 'center',
  },
  featureCard: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    gap: 12,
    padding: '24px 28px',
    borderRadius: 'var(--radius-md)',
    minWidth: 150,
    flex: '1 1 0',
    maxWidth: 200,
  },
  featureIcon: {
    fontSize: 28,
  },
  featureLabel: {
    fontSize: 14,
    fontWeight: 500,
    color: 'var(--text-primary)',
    lineHeight: 1.3,
  },
  actions: {
    marginTop: 8,
  },
  actionBtn: {
    minWidth: 180,
    padding: '14px 36px',
    fontSize: 17,
  },
  finalActions: {
    display: 'flex',
    gap: 16,
    flexWrap: 'wrap',
    justifyContent: 'center',
  },
  dots: {
    position: 'fixed',
    bottom: 48,
    left: '50%',
    transform: 'translateX(-50%)',
    display: 'flex',
    gap: 10,
    zIndex: 51,
  },
  dot: {
    width: 8,
    height: 8,
    borderRadius: '50%',
    border: 'none',
    background: 'var(--text-muted)',
    cursor: 'pointer',
    padding: 0,
    transition: 'all 0.4s cubic-bezier(0.16,1,0.3,1)',
  },
  dotActive: {
    background: 'var(--accent)',
    width: 24,
    borderRadius: 'var(--radius-full)',
    boxShadow: '0 0 12px var(--accent-glow)',
  },
};
