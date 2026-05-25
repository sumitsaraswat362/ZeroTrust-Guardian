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
        <link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>🛡️</text></svg>" />
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
  const [engineStatus, setEngineStatus] = useState('Checking...');
  const [isOnline, setIsOnline] = useState(null); // null = checking, true = online, false = offline

  useEffect(() => {
    const checkHealth = async () => {
      try {
        const res = await fetch('http://localhost:8000/health', { signal: AbortSignal.timeout(3000) });
        if (res.ok) {
          setEngineStatus('Engine Online');
          setIsOnline(true);
        } else {
          setEngineStatus('Cloud Mode');
          setIsOnline(false);
        }
      } catch (e) {
        // On deployed site or when backend isn't running
        setEngineStatus('Cloud Mode');
        setIsOnline(false);
      }
    };
    
    checkHealth();
    const interval = setInterval(checkHealth, 30000);
    return () => clearInterval(interval);
  }, []);

  const navItems = [
    { href: '/', label: 'Overview' },
    { href: '/scan', label: 'Check Link' },
    { href: '/get-extension', label: 'Add to Chrome' },
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

        {/* Status indicator — shows context-appropriate status */}
        <div className="nav-status">
          {isOnline === true && (
            <>
              <span className="status-dot running" />
              <span className="status-text">Engine Online</span>
            </>
          )}
          {isOnline === false && (
            <>
              <span className="status-dot" style={{ background: 'var(--info)', boxShadow: '0 0 8px var(--info)' }} />
              <span className="status-text" style={{ color: 'var(--info)' }}>Landing Page</span>
            </>
          )}
          {isOnline === null && (
            <>
              <span className="status-dot" style={{ background: 'var(--text-muted)' }} />
              <span className="status-text">Connecting...</span>
            </>
          )}
        </div>
      </div>
    </header>
  );
}
