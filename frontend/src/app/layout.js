'use client';

import { useState, useEffect } from 'react';
import './globals.css';
import { usePathname } from 'next/navigation';
import Link from 'next/link';

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <head>
        <title>ZeroTrust Guardian — Your AI Shield Against Online Threats</title>
        <meta name="description" content="ZeroTrust Guardian is an AI-powered Chrome extension that silently protects you from scams, phishing, and deceptive websites as you browse." />
        <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover" />
      </head>
      <body>
        {/* Apple-style breathing mesh background */}
        <div className="mesh-bg">
          <div className="mesh-blob blob-1"></div>
          <div className="mesh-blob blob-2"></div>
          <div className="mesh-blob blob-3"></div>
          <div className="mesh-blob blob-4"></div>
        </div>
        
        <div className="app-layout">
          <TopNav />
          <main className="main-content">
            {children}
          </main>
        </div>
      </body>
    </html>
  );
}

function TopNav() {
  const pathname = usePathname();
  const [engineStatus, setEngineStatus] = useState('Connecting...');
  const [isOnline, setIsOnline] = useState(false);

  useEffect(() => {
    const checkHealth = async () => {
      try {
        const res = await fetch('http://localhost:8000/health');
        if (res.ok) {
          setEngineStatus('Engine Online');
          setIsOnline(true);
        } else {
          setEngineStatus('Engine Offline');
          setIsOnline(false);
        }
      } catch (e) {
        setEngineStatus('Engine Offline');
        setIsOnline(false);
      }
    };
    
    checkHealth();
    const interval = setInterval(checkHealth, 10000);
    return () => clearInterval(interval);
  }, []);

  const navItems = [
    { href: '/', label: 'Overview' },
    { href: '/scan', label: 'Check Link' },
    { href: '/reports', label: 'History' },
  ];

  return (
    <header className="top-nav">
      <div className="nav-container">
        {/* Brand */}
        <Link href="/" className="nav-brand">
          <div className="brand-icon">🛡️</div>
          <div className="brand-text">ZeroTrust</div>
        </Link>

        {/* Links */}
        <nav className="nav-links">
          {navItems.map((item) => {
            const isActive = pathname === item.href || (item.href !== '/' && pathname.startsWith(item.href));
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`nav-item ${isActive ? 'active' : ''}`}
              >
                {item.label}
              </Link>
            );
          })}
        </nav>

        {/* Status indicator */}
        <div className="nav-status">
          <span className={`status-dot ${isOnline ? 'running' : 'failed'}`} />
          <span className="status-text">{engineStatus}</span>
          <Link href="/get-extension" className="btn btn-primary" style={{ padding: '6px 14px', fontSize: '13px', marginLeft: '12px' }}>
            Add to Chrome
          </Link>
        </div>
      </div>
    </header>
  );
}
