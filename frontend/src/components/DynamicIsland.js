'use client';

import { useEffect, useState } from 'react';

export default function DynamicIsland({ message, isVisible, onClose }) {
  const [render, setRender] = useState(false);
  const [expand, setExpand] = useState(false);

  useEffect(() => {
    if (isVisible) {
      setRender(true);
      // Small delay to allow initial DOM render before triggering expansion transition
      const t1 = setTimeout(() => setExpand(true), 10);
      const t2 = setTimeout(() => {
        setExpand(false);
        setTimeout(() => {
          setRender(false);
          if (onClose) onClose();
        }, 500); // Wait for collapse animation
      }, 3000); // How long it stays open
      return () => { clearTimeout(t1); clearTimeout(t2); };
    } else {
      setExpand(false);
      const t = setTimeout(() => setRender(false), 500);
      return () => clearTimeout(t);
    }
  }, [isVisible, onClose]);

  if (!render) return null;

  return (
    <div style={{
      position: 'fixed',
      top: '20px',
      left: '50%',
      transform: 'translateX(-50%)',
      zIndex: 9999,
      pointerEvents: 'none',
    }}>
      <div style={{
        background: 'rgba(0, 0, 0, 0.85)',
        backdropFilter: 'blur(20px) saturate(180%)',
        WebkitBackdropFilter: 'blur(20px) saturate(180%)',
        borderRadius: '30px',
        padding: '0',
        height: '40px',
        width: expand ? '220px' : '40px',
        transition: 'width 0.5s cubic-bezier(0.16, 1, 0.3, 1)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        boxShadow: '0 10px 40px rgba(0,0,0,0.5), inset 0 1px 0 rgba(255,255,255,0.1)',
        overflow: 'hidden',
        border: '1px solid rgba(255,255,255,0.1)',
      }}>
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          opacity: expand ? 1 : 0,
          transition: 'opacity 0.3s ease-in-out',
          transitionDelay: expand ? '0.2s' : '0s',
          whiteSpace: 'nowrap',
          color: '#fff',
          fontSize: '14px',
          fontWeight: '500',
          letterSpacing: '-0.01em',
        }}>
          {message}
        </div>
      </div>
    </div>
  );
}
