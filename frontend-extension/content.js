/**
 * ZeroTrust Guardian — Content Script
 * 
 * Injects a minimal, non-intrusive floating indicator into every page.
 * Apple Design: Invisible until needed. Beautifully informative when present.
 * Uses requestAnimationFrame for DOM batching per Chrome extension best practices.
 */

const INDICATOR_ID = 'zt-guardian-shield';
let currentResult = null;

// ─── Listen for messages from background ────────────────────────────────────
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'show_indicator') {
    currentResult = request.result;
    requestAnimationFrame(() => {
      renderIndicator(request.result);
    });
  }
});

// ─── Render the floating trust indicator ────────────────────────────────────
function renderIndicator(result) {
  // Remove existing
  const existing = document.getElementById(INDICATOR_ID);
  if (existing) existing.remove();

  const container = document.createElement('div');
  container.id = INDICATOR_ID;
  container.setAttribute('role', 'status');
  container.setAttribute('aria-live', 'polite');

  const { status, trustScore, reason } = result;

  // Determine visual state
  let config;
  switch (status) {
    case 'danger':
    case 'scam':
      config = {
        icon: '🛑',
        label: 'Threat Detected',
        color: '#ef4444',
        glow: 'rgba(239, 68, 68, 0.4)',
        bgGradient: 'linear-gradient(135deg, rgba(127, 29, 29, 0.95), rgba(153, 27, 27, 0.92))',
        pulse: true,
        autoHide: false,
      };
      break;
    case 'warning':
      config = {
        icon: '⚠️',
        label: 'Caution',
        color: '#f59e0b',
        glow: 'rgba(245, 158, 11, 0.3)',
        bgGradient: 'linear-gradient(135deg, rgba(120, 53, 15, 0.95), rgba(146, 64, 14, 0.92))',
        pulse: false,
        autoHide: false,
      };
      break;
    case 'analyzing':
      config = {
        icon: '🔍',
        label: 'Analyzing',
        color: '#818cf8',
        glow: 'rgba(129, 140, 248, 0.3)',
        bgGradient: 'linear-gradient(135deg, rgba(30, 27, 75, 0.95), rgba(49, 46, 129, 0.92))',
        pulse: true,
        autoHide: false,
      };
      break;
    case 'unknown':
      config = {
        icon: '❓',
        label: 'Offline',
        color: '#64748b',
        glow: 'rgba(100, 116, 139, 0.2)',
        bgGradient: 'linear-gradient(135deg, rgba(30, 41, 59, 0.95), rgba(51, 65, 85, 0.92))',
        pulse: false,
        autoHide: true,
      };
      break;
    default: // 'safe'
      config = {
        icon: '🛡️',
        label: 'Verified Safe',
        color: '#10b981',
        glow: 'rgba(16, 185, 129, 0.3)',
        bgGradient: 'linear-gradient(135deg, rgba(6, 78, 59, 0.95), rgba(4, 120, 87, 0.92))',
        pulse: false,
        autoHide: true,
      };
  }

  // Build the floating pill
  const scoreText = trustScore !== null && trustScore !== undefined ? `${trustScore}%` : '--';

  container.innerHTML = `
    <div class="zt-shield-inner">
      <div class="zt-shield-icon">${config.icon}</div>
      <div class="zt-shield-content">
        <div class="zt-shield-label">${config.label}</div>
        <div class="zt-shield-score" style="color: ${config.color}">${scoreText}</div>
      </div>
      <div class="zt-shield-expand" aria-label="More details">
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="6 9 12 15 18 9"></polyline></svg>
      </div>
    </div>
    <div class="zt-shield-detail" style="display: none;">
      <div class="zt-shield-reason">${escapeHtml(reason || 'No details available.')}</div>
      ${result.threats && result.threats.length > 0 ? `
        <div class="zt-shield-threats">
          ${result.threats.slice(0, 3).map(t => `
            <div class="zt-shield-threat-item">
              <span class="zt-shield-threat-dot" style="background: ${getSeverityColor(t.severity)}"></span>
              <span>${escapeHtml(t.title || t.type || 'Unknown threat')}</span>
            </div>
          `).join('')}
        </div>
      ` : ''}
    </div>
  `;

  // Apply dynamic styles to container via inline (no CSS var conflicts with host page)
  Object.assign(container.style, {
    position: 'fixed',
    bottom: '20px',
    right: '20px',
    zIndex: '2147483647',
    fontFamily: '-apple-system, BlinkMacSystemFont, "SF Pro Display", "Segoe UI", Roboto, Helvetica, Arial, sans-serif',
    fontSize: '13px',
    lineHeight: '1.4',
    color: '#f8fafc',
    borderRadius: '16px',
    background: config.bgGradient,
    backdropFilter: 'blur(20px) saturate(180%)',
    WebkitBackdropFilter: 'blur(20px) saturate(180%)',
    boxShadow: `0 8px 32px rgba(0,0,0,0.3), 0 0 0 1px rgba(255,255,255,0.08), 0 0 20px ${config.glow}`,
    border: `1px solid rgba(255,255,255,0.1)`,
    cursor: 'pointer',
    transition: 'all 0.4s cubic-bezier(0.16, 1, 0.3, 1)',
    opacity: '0',
    transform: 'translateY(12px) scale(0.95)',
    maxWidth: '320px',
    overflow: 'hidden',
  });

  document.body.appendChild(container);

  // Animate in
  requestAnimationFrame(() => {
    requestAnimationFrame(() => {
      container.style.opacity = '1';
      container.style.transform = 'translateY(0) scale(1)';
    });
  });

  // Pulse animation for danger/analyzing
  if (config.pulse) {
    container.classList.add('zt-pulse');
  }

  // Click to expand
  let expanded = false;
  const inner = container.querySelector('.zt-shield-inner');
  const detail = container.querySelector('.zt-shield-detail');
  const expandIcon = container.querySelector('.zt-shield-expand');

  if (inner) {
    inner.addEventListener('click', (e) => {
      e.stopPropagation();
      expanded = !expanded;
      if (detail) detail.style.display = expanded ? 'block' : 'none';
      if (expandIcon) expandIcon.style.transform = expanded ? 'rotate(180deg)' : 'rotate(0deg)';
    });
  }

  // Auto-hide safe/unknown indicators after delay
  if (config.autoHide) {
    setTimeout(() => {
      container.style.opacity = '0';
      container.style.transform = 'translateY(12px) scale(0.95)';
      setTimeout(() => container.remove(), 400);
    }, 5000);
  }
}

// ─── Helpers ────────────────────────────────────────────────────────────────
function escapeHtml(str) {
  const div = document.createElement('div');
  div.textContent = str;
  return div.innerHTML;
}

function getSeverityColor(severity) {
  const colors = {
    critical: '#ef4444',
    high: '#f97316',
    medium: '#f59e0b',
    low: '#3b82f6',
    info: '#6b7280',
  };
  return colors[severity] || '#6b7280';
}
