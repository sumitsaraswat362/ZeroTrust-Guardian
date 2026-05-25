'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';

export default function HistoryPage() {
  const [reports, setReports] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchReports() {
      try {
        const res = await fetch('http://localhost:8000/api/reports');
        if (res.ok) {
          const data = await res.json();
          setReports(data.reports || []);
        }
      } catch (e) {
        console.error('Failed to fetch reports:', e);
      } finally {
        setLoading(false);
      }
    }
    fetchReports();
  }, []);

  return (
    <div className="animate-in">
      <div className="page-header">
        <h2>Safety History</h2>
        <p>Your complete browsing safety analysis history.</p>
      </div>

      {loading ? (
        <div style={{ textAlign: 'center', padding: '80px 0' }}>
          <div className="spinner" style={{ margin: '0 auto' }} />
        </div>
      ) : reports.length === 0 ? (
        <div className="glass-card" style={{ textAlign: 'center', padding: '80px 40px' }}>
          <div style={{ fontSize: '56px', marginBottom: '16px', opacity: 0.5 }}>📋</div>
          <h3 style={{ fontSize: '22px', fontWeight: 600, marginBottom: '8px', color: 'var(--text-secondary)' }}>
            No history yet
          </h3>
          <p style={{ fontSize: '17px', color: 'var(--text-muted)', marginBottom: '24px' }}>
            Analyze a link to start building your safety history.
          </p>
          <Link href="/scan" className="btn btn-primary">
            Check a Link
          </Link>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          {reports.map((report) => (
            <Link key={report.scan_id} href={`/reports/detail?id=${report.scan_id}`} style={{ textDecoration: 'none', color: 'inherit' }}>
              <div className="glass-card" style={{ padding: '24px', cursor: 'pointer' }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <div>
                    <div style={{ fontSize: '17px', fontWeight: 600 }}>{report.target_url}</div>
                    <div style={{ fontSize: '14px', color: 'var(--text-muted)', marginTop: '4px' }}>
                      {new Date(report.completed_at).toLocaleDateString()} · {report.scan_duration_seconds}s · {report.pages_crawled} pages
                    </div>
                  </div>
                  <div style={{
                    padding: '6px 16px', borderRadius: 'var(--radius-full)',
                    fontSize: '13px', fontWeight: 600,
                    background: report.risk_score >= 50 ? 'rgba(255,59,48,0.15)' : 'rgba(50,215,75,0.15)',
                    color: report.risk_score >= 50 ? '#ff3b30' : '#32d74b',
                  }}>
                    Risk: {report.risk_score}
                  </div>
                </div>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
