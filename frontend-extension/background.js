/**
 * ZeroTrust Guardian — Service Worker (Background Script)
 * 
 * Apple Design Philosophy: Complex technology, invisible to the user.
 * This service worker silently analyzes every page the user visits,
 * persists state in chrome.storage (never global variables), and
 * communicates results to the content script and popup.
 */

const API_BASE = 'http://localhost:8000';

// ─── Event: Tab navigation completed ────────────────────────────────────────
chrome.tabs.onUpdated.addListener(async (tabId, changeInfo, tab) => {
  if (changeInfo.status !== 'complete') return;
  if (!tab.url || tab.url.startsWith('chrome://') || tab.url.startsWith('chrome-extension://') || tab.url.startsWith('about:')) return;

  await analyzePage(tab.url, tabId);
});

// ─── Core Analysis Function ─────────────────────────────────────────────────
async function analyzePage(url, tabId) {
  // Set loading state
  await chrome.storage.local.set({
    [`tab_${tabId}`]: {
      url,
      status: 'analyzing',
      timestamp: Date.now(),
      trustScore: null,
      threats: [],
      reason: 'Analyzing this page...'
    }
  });

  // Update badge to show loading
  await chrome.action.setBadgeText({ text: '...', tabId });
  await chrome.action.setBadgeBackgroundColor({ color: '#6366f1', tabId });

  // Notify content script to show loading indicator
  try {
    await chrome.tabs.sendMessage(tabId, {
      action: 'show_indicator',
      result: { status: 'analyzing', reason: 'Scanning page for threats...', trustScore: null }
    });
  } catch (_) { /* Content script not ready yet */ }

  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 30000);

    const response = await fetch(`${API_BASE}/api/v1/analyze`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ url }),
      signal: controller.signal,
    });
    clearTimeout(timeoutId);

    if (!response.ok) {
      throw new Error(`Server responded with ${response.status}`);
    }

    const data = await response.json();

    // Persist result
    const result = {
      url,
      status: data.status || 'safe',
      trustScore: data.trust_score ?? 100,
      threats: data.threats || [],
      reason: data.reason || 'No threats detected.',
      details: data.details || {},
      timestamp: Date.now(),
    };

    await chrome.storage.local.set({ [`tab_${tabId}`]: result });

    // Update badge
    const badgeConfig = getBadgeConfig(result.status, result.trustScore);
    await chrome.action.setBadgeText({ text: badgeConfig.text, tabId });
    await chrome.action.setBadgeBackgroundColor({ color: badgeConfig.color, tabId });

    // Notify content script
    try {
      await chrome.tabs.sendMessage(tabId, {
        action: 'show_indicator',
        result,
      });
    } catch (_) { /* Content script may not be injected */ }

  } catch (error) {
    console.error('ZeroTrust Guardian analysis failed:', error.message);

    const fallback = {
      url,
      status: 'unknown',
      trustScore: null,
      threats: [],
      reason: 'Unable to reach analysis server. Please ensure the backend is running.',
      timestamp: Date.now(),
    };
    await chrome.storage.local.set({ [`tab_${tabId}`]: fallback });
    await chrome.action.setBadgeText({ text: '?', tabId });
    await chrome.action.setBadgeBackgroundColor({ color: '#64748b', tabId });

    try {
      await chrome.tabs.sendMessage(tabId, { action: 'show_indicator', result: fallback });
    } catch (_) { /* */ }
  }
}

// ─── Badge Configuration ────────────────────────────────────────────────────
function getBadgeConfig(status, trustScore) {
  if (status === 'danger' || status === 'scam') {
    return { text: '!', color: '#ef4444' };
  }
  if (status === 'warning') {
    return { text: '!', color: '#f59e0b' };
  }
  if (status === 'safe') {
    return { text: '✓', color: '#10b981' };
  }
  return { text: '?', color: '#64748b' };
}

// ─── Message Handler (from popup or content script) ─────────────────────────
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.action === 'get_status') {
    (async () => {
      const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
      if (tab) {
        const data = await chrome.storage.local.get(`tab_${tab.id}`);
        sendResponse(data[`tab_${tab.id}`] || null);
      } else {
        sendResponse(null);
      }
    })();
    return true; // Keep channel open for async response
  }

  if (message.action === 'rescan') {
    (async () => {
      const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
      if (tab && tab.url) {
        await analyzePage(tab.url, tab.id);
        const data = await chrome.storage.local.get(`tab_${tab.id}`);
        sendResponse(data[`tab_${tab.id}`] || null);
      } else {
        sendResponse(null);
      }
    })();
    return true;
  }
});

// ─── Cleanup old data periodically ──────────────────────────────────────────
chrome.alarms.create('cleanup', { periodInMinutes: 30 });
chrome.alarms.onAlarm.addListener(async (alarm) => {
  if (alarm.name === 'cleanup') {
    const all = await chrome.storage.local.get(null);
    const now = Date.now();
    const keysToRemove = [];
    for (const [key, value] of Object.entries(all)) {
      if (key.startsWith('tab_') && value.timestamp && (now - value.timestamp > 3600000)) {
        keysToRemove.push(key);
      }
    }
    if (keysToRemove.length > 0) {
      await chrome.storage.local.remove(keysToRemove);
    }
  }
});
