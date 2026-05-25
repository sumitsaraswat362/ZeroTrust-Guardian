/**
 * ZeroTrust Guardian — Popup Script
 * 
 * Reads cached analysis from chrome.storage and renders the trust score,
 * status banner, and threat details. Uses async/await per MV3 best practices.
 */

document.addEventListener('DOMContentLoaded', async () => {
  const scoreNumber = document.getElementById('score-number');
  const scoreRing = document.getElementById('score-ring-progress');
  const statusBanner = document.getElementById('status-banner');
  const statusIcon = document.getElementById('status-icon');
  const statusTitle = document.getElementById('status-title');
  const statusReason = document.getElementById('status-reason');
  const threatsSection = document.getElementById('threats-section');
  const threatsList = document.getElementById('threats-list');
  const currentUrl = document.getElementById('current-url');
  const rescanBtn = document.getElementById('rescan-btn');

  const RING_CIRCUMFERENCE = 2 * Math.PI * 58; // r=58

  // ─── Load Data ──────────────────────────────────────────────────────
  async function loadData() {
    return new Promise((resolve) => {
      chrome.runtime.sendMessage({ action: 'get_status' }, (response) => {
        resolve(response);
      });
    });
  }

  // ─── Render ─────────────────────────────────────────────────────────
  function render(data) {
    if (!data) {
      scoreNumber.textContent = '--';
      statusTitle.textContent = 'No Data';
      statusReason.textContent = 'Navigate to a website to begin analysis.';
      currentUrl.textContent = 'No active tab';
      return;
    }

    // URL
    try {
      const url = new URL(data.url);
      currentUrl.textContent = url.hostname + url.pathname;
    } catch {
      currentUrl.textContent = data.url || 'Unknown';
    }

    // Trust Score
    const score = data.trustScore;
    if (score !== null && score !== undefined) {
      animateScore(score);
    } else {
      scoreNumber.textContent = '--';
      scoreRing.style.strokeDashoffset = RING_CIRCUMFERENCE;
    }

    // Status Banner
    const statusConfig = getStatusConfig(data.status, score);
    statusBanner.className = `status-banner status-${statusConfig.class}`;
    statusIcon.textContent = statusConfig.icon;
    statusTitle.textContent = statusConfig.title;
    statusReason.textContent = data.reason || 'No details available.';

    // Ring color
    scoreRing.style.stroke = statusConfig.ringColor;

    // Threats
    if (data.threats && data.threats.length > 0) {
      threatsSection.style.display = 'block';
      threatsList.innerHTML = '';
      data.threats.forEach(threat => {
        const item = document.createElement('div');
        item.className = 'threat-item';
        const severity = (threat.severity || 'info').toLowerCase();
        item.innerHTML = `
          <span class="threat-severity ${severity}"></span>
          <span class="threat-text">${escapeHtml(threat.title || threat.type || 'Unknown')}</span>
          <span class="threat-badge ${severity}">${severity}</span>
        `;
        threatsList.appendChild(item);
      });
    } else {
      threatsSection.style.display = 'none';
    }
  }

  // ─── Animate Score Counter ──────────────────────────────────────────
  function animateScore(target) {
    const duration = 1200;
    const start = performance.now();
    const startVal = 0;

    function frame(now) {
      const elapsed = now - start;
      const progress = Math.min(elapsed / duration, 1);
      // Ease out cubic
      const ease = 1 - Math.pow(1 - progress, 3);
      const current = Math.round(startVal + (target - startVal) * ease);

      scoreNumber.textContent = current;

      // Ring
      const offset = RING_CIRCUMFERENCE - (RING_CIRCUMFERENCE * current / 100);
      scoreRing.style.strokeDashoffset = offset;

      if (progress < 1) {
        requestAnimationFrame(frame);
      }
    }

    requestAnimationFrame(frame);
  }

  // ─── Status Config ─────────────────────────────────────────────────
  function getStatusConfig(status, score) {
    switch (status) {
      case 'danger':
      case 'scam':
        return { class: 'danger', icon: '🛑', title: 'Threat Detected', ringColor: '#ef4444' };
      case 'warning':
        return { class: 'warning', icon: '⚠️', title: 'Caution Advised', ringColor: '#f59e0b' };
      case 'analyzing':
        return { class: 'analyzing', icon: '🔍', title: 'Analyzing...', ringColor: '#818cf8' };
      case 'unknown':
        return { class: 'analyzing', icon: '❓', title: 'Offline', ringColor: '#64748b' };
      default:
        if (score !== null && score < 50) {
          return { class: 'warning', icon: '⚠️', title: 'Low Trust Score', ringColor: '#f59e0b' };
        }
        return { class: 'safe', icon: '🛡️', title: 'Verified Safe', ringColor: '#10b981' };
    }
  }

  // ─── Rescan Button ─────────────────────────────────────────────────
  rescanBtn.addEventListener('click', async () => {
    rescanBtn.classList.add('spinning');
    rescanBtn.disabled = true;

    // Reset UI to loading state
    scoreNumber.textContent = '--';
    scoreRing.style.strokeDashoffset = RING_CIRCUMFERENCE;
    statusBanner.className = 'status-banner status-analyzing';
    statusIcon.textContent = '🔍';
    statusTitle.textContent = 'Re-scanning...';
    statusReason.textContent = 'Running fresh analysis...';
    threatsSection.style.display = 'none';

    const result = await new Promise((resolve) => {
      chrome.runtime.sendMessage({ action: 'rescan' }, (response) => {
        resolve(response);
      });
    });

    // Wait a moment for the scan to complete, then reload
    setTimeout(async () => {
      const freshData = await loadData();
      render(freshData);
      rescanBtn.classList.remove('spinning');
      rescanBtn.disabled = false;
    }, 3000);
  });

  // ─── Helpers ───────────────────────────────────────────────────────
  function escapeHtml(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
  }

  // ─── Initial Load ──────────────────────────────────────────────────
  const data = await loadData();
  render(data);
});
