# 🛡️ ZeroTrust Guardian

**Your AI-Powered Digital Guardian Against Online Threats**

ZeroTrust Guardian is a consumer-grade, AI-powered security product that protects everyday internet users from scams, phishing, dark patterns, and deceptive websites — automatically, silently, and in real time.

> *"Complex technology, invisible to the user."* — Built with Apple's design philosophy.

---

## 🎯 The Problem

Every day, millions of people fall victim to:
- **Phishing sites** that steal passwords and personal data
- **Dark patterns** that manipulate users into unwanted purchases
- **Fake virus warnings** and tech support scams
- **Insecure websites** that leak personal data

Normal users don't run vulnerability scanners. They need **invisible, automatic protection**.

## 💡 The Solution

ZeroTrust Guardian is a **Chrome Extension** that sits silently in your browser and analyzes every page you visit using a multi-agent AI system. When a threat is detected, you're immediately warned with a clear, non-technical explanation.

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│  Chrome Extension (Consumer Frontend)                    │
│  ├── background.js (Service Worker — triggers analysis)  │
│  ├── content.js (Floating trust indicator)               │
│  └── popup/ (Premium glassmorphism popup)                │
└─────────────────┬───────────────────────────────────────┘
                  │ REST API
                  ▼
┌─────────────────────────────────────────────────────────┐
│  FastAPI Backend (AI Analysis Engine)                    │
│  ├── /api/v1/analyze (Quick analysis for extension)      │
│  ├── /api/scan (Full deep scan)                          │
│  └── Multi-Agent Orchestrator                            │
│      ├── Recon Agent (Crawling + Surface Mapping)        │
│      ├── Scam Detection Agent (Dark patterns + Phishing) │
│      ├── Vuln Scanner Agent (Headers + CORS + XSS)       │
│      └── Report Agent (Gemini AI-powered summaries)      │
└─────────────────┬───────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────┐
│  Google Gemini AI (Consumer-friendly threat summaries)    │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│  Next.js Dashboard (Product Landing Page + Web Scanner)  │
│  ├── / (Hero + Features + CTA)                           │
│  ├── /scan (Check a Link)                                │
│  └── /reports (Safety History)                            │
└─────────────────────────────────────────────────────────┘
```

## 🔍 What It Detects

| Threat Type | How |
|---|---|
| **Phishing & Scam Sites** | URL pattern analysis, domain age, suspicious TLDs, typosquatting detection |
| **Dark Patterns** | Regex-based content analysis: fake urgency, artificial scarcity, scare tactics |
| **Insecure Connections** | SSL certificate validation, HTTPS enforcement checks |
| **Missing Security Headers** | CSP, HSTS, X-Frame-Options, X-Content-Type-Options |
| **Hidden Tracking** | External script counting, hidden iframe detection |
| **Password Theft Risk** | Detects password fields on non-HTTPS pages |

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- Google Chrome

### 1. Start the Backend

```bash
cd backend
pip install -r requirements.txt
playwright install chromium
uvicorn main:app --reload --port 8000
```

### 2. Start the Frontend (Landing Page)

```bash
cd frontend
npm install
npm run dev
```

### 3. Load the Chrome Extension

1. Open `chrome://extensions` in Chrome
2. Enable **Developer mode** (top right)
3. Click **Load unpacked**
4. Select the `frontend-extension/` folder
5. Browse to any website — the extension activates automatically!

### 4. (Optional) Start the Vulnerable Test App

```bash
cd vulnerable-app
npm install
node server.js
```

Then analyze `http://localhost:4000` through the extension or the web dashboard.

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| **Extension** | Chrome Extension Manifest V3, vanilla JS |
| **Frontend** | Next.js 14, React, Vanilla CSS, Glassmorphism |
| **Backend** | FastAPI, Python 3.11+, Playwright, httpx |
| **AI** | Google Gemini 2.5 Flash |
| **Architecture** | Multi-Agent Orchestration, WebSocket streaming |

## 📱 Design Philosophy

This project follows **Apple's Human Interface Guidelines** principles:

1. **Invisible Complexity** — The multi-agent AI architecture runs 6 parallel security checks in under 10 seconds, but the user only sees a simple colored indicator.
2. **Deference** — The UI stays out of the way. Safe sites show a brief green indicator that auto-fades. Only threats demand attention.
3. **Clarity** — Threat descriptions use plain English, not security jargon. "This site has a missing security header" becomes "Your data may not be fully protected on this site."
4. **Depth** — Every layer rewards closer inspection. The floating indicator expands to show details. The popup shows a trust score ring. The dashboard shows deep analysis.

---

## 📄 License

Built for Microsoft Build AI 2026 Hackathon & Apple Developer Academy application.
