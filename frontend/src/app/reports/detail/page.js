'use client';

import { useState, useEffect, Suspense } from 'react';
import { useSearchParams } from 'next/navigation';
import Link from 'next/link';

function ReportDetailContent() {
  const searchParams = useSearchParams();
  const scanId = searchParams.get('id');
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(true);
  const [expandedVuln, setExpandedVuln] = useState(null);

  useEffect(() => {
    if (scanId) {
      fetchReport();
    } else {
      setLoading(false);
    }
  }, [scanId]);

  async function fetchReport() {
    try {
      const res = await fetch(`http://localhost:8000/api/reports/${scanId}`);
      if (res.ok) {
        setReport(await res.json());
      }
    } catch (e) {
      console.error('Failed to fetch report:', e);
    } finally {
      setLoading(false);
    }
  }

  if (loading) {
    return <div className="empty-state"><div className="spinner" style={{ margin: '0 auto', width: '40px', height: '40px' }} /></div>;
  }

  if (!report) {
    return (
      <div className="glass-card">
        <div className="empty-state">
          <div className="icon">❌</div>
          <h3>Report not found</h3>
          <p>The scan may still be in progress</p>
          <Link href={`/scan/${scanId}`} className="btn btn-primary" style={{ marginTop: '16px' }}>View Scan Progress</Link>
        </div>
      </div>
    );
  }

  const riskColorCss = report.risk_score >= 75 ? 'var(--critical)' :
                     report.risk_score >= 50 ? 'var(--high)' :
                     report.risk_score >= 25 ? 'var(--medium)' : 'var(--low)';
                     
  const riskColorHex = report.risk_score >= 75 ? '#ef4444' :
                     report.risk_score >= 50 ? '#f97316' :
                     report.risk_score >= 25 ? '#eab308' : '#3b82f6';

  const circumference = 2 * Math.PI * 75;
  const dashOffset = circumference - (report.risk_score / 100) * circumference;

  return (
    <div>
      <div className="page-header animate-in">
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '4px' }}>
          <Link href="/reports" style={{ color: 'var(--text-muted)', fontSize: '14px' }}>← Reports</Link>
        </div>
        <h2>Security Report</h2>
        <p style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: '12px', color: 'var(--text-muted)' }}>
          {report.target_url} • {new Date(report.completed_at).toLocaleString()}
        </p>
      </div>

      {/* Executive Summary */}
      <div style={{ display: 'grid', gridTemplateColumns: '220px 1fr', gap: '24px', marginBottom: '24px' }}>
        {/* Risk Gauge */}
        <div className="glass-card animate-in animate-in-delay-1" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <div className="risk-gauge">
            <svg viewBox="0 0 180 180">
              <circle className="track" cx="90" cy="90" r="75" />
              <circle className="progress" cx="90" cy="90" r="75"
                stroke={riskColorHex}
                style={{
                  stroke: riskColorHex,
                  strokeDasharray: circumference,
                  strokeDashoffset: dashOffset,
                }}
              />
            </svg>
            <div className="score-label">
              <div className="score-value" style={{ color: riskColorCss }}>{report.risk_score}</div>
              <div className="score-text">{report.risk_level}</div>
            </div>
          </div>
        </div>

        {/* Summary */}
        <div className="glass-card animate-in animate-in-delay-2">
          <h3 style={{ fontSize: '16px', fontWeight: 700, marginBottom: '12px' }}>Executive Summary</h3>
          <p style={{ fontSize: '14px', color: 'var(--text-secondary)', lineHeight: 1.7, whiteSpace: 'pre-line' }}>
            {report.executive_summary}
          </p>
        </div>
      </div>

      {/* Statistics */}
      <div className="stats-grid animate-in animate-in-delay-3">
        <div className="stat-card">
          <div className="stat-icon">⚠️</div>
          <div className="stat-value">{report.statistics?.total_vulnerabilities || 0}</div>
          <div className="stat-label">Total Vulnerabilities</div>
        </div>
        <div className="stat-card">
          <div className="stat-icon">📄</div>
          <div className="stat-value">{report.statistics?.pages_crawled || 0}</div>
          <div className="stat-label">Pages Crawled</div>
        </div>
        <div className="stat-card">
          <div className="stat-icon">🎯</div>
          <div className="stat-value">{report.statistics?.endpoints_tested || 0}</div>
          <div className="stat-label">Endpoints Tested</div>
        </div>
        <div className="stat-card">
          <div className="stat-icon">⏱️</div>
          <div className="stat-value">{report.scan_duration_seconds}s</div>
          <div className="stat-label">Scan Duration</div>
        </div>
      </div>

      {/* Severity Breakdown */}
      {report.statistics?.by_severity && (
        <div className="glass-card animate-in animate-in-delay-4" style={{ marginBottom: '24px' }}>
          <h3 style={{ fontSize: '16px', fontWeight: 700, marginBottom: '16px' }}>Severity Distribution</h3>
          <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
            {Object.entries(report.statistics.by_severity).map(([severity, count]) => {
              const total = report.statistics.total_vulnerabilities || 1;
              const pct = Math.round((count / total) * 100);
              return (
                <div key={severity} style={{
                  flex: '1 1 120px', padding: '16px',
                  background: `var(--${severity}-bg)`, borderRadius: 'var(--radius-md)',
                  textAlign: 'center', minWidth: '100px',
                }}>
                  <div style={{ fontSize: '28px', fontWeight: 800, color: `var(--${severity})` }}>{count}</div>
                  <div style={{ fontSize: '12px', fontWeight: 600, color: `var(--${severity})`, textTransform: 'capitalize' }}>{severity}</div>
                  <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '2px' }}>{pct}%</div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Remediation Plan */}
      {report.remediation_plan?.length > 0 && (
        <div className="glass-card animate-in" style={{ marginBottom: '24px' }}>
          <h3 style={{ fontSize: '16px', fontWeight: 700, marginBottom: '16px' }}>🔧 Remediation Plan</h3>
          {report.remediation_plan.map((item, i) => (
            <div key={i} style={{
              display: 'flex', gap: '14px', alignItems: 'flex-start',
              padding: '14px', marginBottom: '8px',
              background: 'var(--glass-bg)', borderRadius: 'var(--radius-md)',
              borderLeft: `3px solid var(--${item.severity})`,
            }}>
              <div style={{
                width: '28px', height: '28px', borderRadius: '50%', flexShrink: 0,
                background: 'var(--accent-muted)', display: 'flex', alignItems: 'center',
                justifyContent: 'center', fontSize: '13px', fontWeight: 800, color: 'var(--accent-hover)',
              }}>
                {item.priority}
              </div>
              <div>
                <div style={{ fontSize: '14px', fontWeight: 600, marginBottom: '4px' }}>{item.title}</div>
                <div style={{ fontSize: '13px', color: 'var(--text-secondary)', lineHeight: 1.6 }}>
                  {item.remediation}
                </div>
              </div>
              <span className={`severity-badge ${item.severity}`} style={{ flexShrink: 0 }}>
                {item.severity}
              </span>
            </div>
          ))}
        </div>
      )}

      {/* Vulnerability Details */}
      {report.vulnerabilities?.length > 0 && (
        <div className="animate-in">
          <h3 style={{ fontSize: '18px', fontWeight: 700, marginBottom: '16px' }}>
            Detailed Findings ({report.vulnerabilities.length})
          </h3>
          {report.vulnerabilities.map((vuln, i) => (
            <div
              key={vuln.id || i}
              className={`vuln-card ${vuln.severity}`}
              onClick={() => setExpandedVuln(expandedVuln === i ? null : i)}
            >
              <div className="vuln-card-header">
                <span className="vuln-card-title">{vuln.title}</span>
                <span className={`severity-badge ${vuln.severity}`}>
                  <span className={`severity-dot ${vuln.severity}`} />
                  {vuln.severity}
                </span>
              </div>
              <div className="vuln-card-desc">{vuln.description}</div>
              <div className="vuln-card-meta">
                <span>📍 {vuln.endpoint}</span>
                <span>🏷️ {vuln.type}</span>
                <span style={{ marginLeft: 'auto', color: 'var(--accent-hover)' }}>
                  {expandedVuln === i ? '▲ Collapse' : '▼ Details'}
                </span>
              </div>

              {expandedVuln === i && (
                <div style={{ marginTop: '12px' }}>
                  {vuln.payload_used && (
                    <div style={{ marginBottom: '10px' }}>
                      <div style={{ fontSize: '12px', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '4px' }}>
                        Payload Used
                      </div>
                      <div className="vuln-card-evidence">{vuln.payload_used}</div>
                    </div>
                  )}
                  {vuln.evidence && (
                    <div style={{ marginBottom: '10px' }}>
                      <div style={{ fontSize: '12px', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '4px' }}>
                        Evidence
                      </div>
                      <div className="vuln-card-evidence">{vuln.evidence}</div>
                    </div>
                  )}
                  {vuln.remediation && (
                    <div>
                      <div style={{ fontSize: '12px', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '4px' }}>
                        Remediation
                      </div>
                      <div style={{
                        padding: '12px', background: 'var(--low-bg)', borderRadius: 'var(--radius-sm)',
                        fontSize: '13px', color: 'var(--low)', lineHeight: 1.6,
                      }}>
                        ✅ {vuln.remediation}
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default function ReportDetail() {
  return (
    <Suspense fallback={<div className="empty-state"><div className="spinner" style={{ margin: '0 auto', width: '40px', height: '40px' }} /></div>}>
      <ReportDetailContent />
    </Suspense>
  );
}
