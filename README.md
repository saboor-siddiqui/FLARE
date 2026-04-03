# ⚡ FLARE — Failure Log Airflow Response Engine

> **AI-powered incident triage for Airflow DAG failures.**  
> Paste a log. Get root cause, a Slack alert, and a stakeholder email — in seconds.

![Python](https://img.shields.io/badge/Python-3.9%2B-blue?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100%2B-009688?logo=fastapi&logoColor=white)
![Anthropic](https://img.shields.io/badge/Claude-AI-blueviolet?logo=anthropic&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green)

---

## What is FLARE?

FLARE is a lightweight, self-hosted AI triage agent for data engineering teams running Apache Airflow. When a DAG fails, instead of digging through raw stack traces manually, you paste the error log into FLARE and the AI (Claude) does the rest:

- 🔍 **Root cause analysis** — identifies the exact failure reason in plain English
- 🚨 **Severity classification** — `CRITICAL / HIGH / MEDIUM / LOW`
- 💬 **Slack message draft** — ready-to-post structured alert with fields, action items, and a code fix snippet
- ✉️ **Email draft** — professional incident email with sections for Summary, Root Cause, Impact, and Action Required
- ⚠️ **Downstream impact** — lists all blocked downstream tasks

---

## Architecture

```
Browser (index.html)
      │
      │  POST /api/triage  (raw Airflow log)
      ▼
FastAPI Server (main.py)
      │
      │  Injects API key server-side
      │  Proxies to Anthropic API
      ▼
Claude (claude-sonnet-4)
      │
      │  Returns structured JSON triage report
      ▼
FastAPI → Browser
      │
      ▼
Renders: Severity strip, Root cause, Slack preview, Email preview, Downstream impact
```

The backend is intentionally minimal — a two-route FastAPI app:
| Route | Method | Purpose |
|-------|--------|---------|
| `/` | `GET` | Serves the single-page UI (`index.html`) |
| `/api/triage` | `POST` | Proxies the log to Anthropic and returns structured JSON |

The API key **never touches the browser** — it lives in `.env` and is injected server-side on every request.

---

## Features

| Feature | Description |
|---------|-------------|
| **AI Root Cause** | Claude analyzes the full stack trace and explains the failure in 1–2 plain-English sentences |
| **Severity Badge** | Automatically classifies as CRITICAL / HIGH / MEDIUM / LOW with color-coded UI |
| **Slack Preview** | Live-rendered Slack-style message with header, summary, key fields, action items, and optional code fix |
| **Email Draft** | Pre-written incident email with professional structure, ready to send to the team |
| **Downstream Impact** | Extracts and displays blocked downstream tasks from the log |
| **Sample Log** | Built-in sample BigQuery / Airflow log for quick demos |
| **Copy Button** | One-click copy of the Slack or email content |
| **Secure API Key** | Key stored in `.env`, never exposed to the client |

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python · FastAPI · Uvicorn |
| HTTP Client | `httpx` (async) |
| AI Model | Anthropic Claude (`claude-sonnet-4`) |
| Frontend | Vanilla HTML/CSS/JS (zero dependencies) |
| Fonts | DM Sans · DM Mono (Google Fonts) |
| Config | `python-dotenv` |

---

## Getting Started

### 1. Clone the repo

```bash
git clone https://github.com/<your-username>/flare.git
cd flare
```

### 2. Create a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Set your Anthropic API key

Create a `.env` file in the project root (it is git-ignored):

```bash
cp .env.example .env
```

Then open `.env` and set your key:

```
ANTHROPIC_API_KEY=sk-ant-...
```

Get your key at: [console.anthropic.com](https://console.anthropic.com)

### 5. Run the server

```bash
uvicorn main:app --reload --port 8000
```

Open **[http://localhost:8000](http://localhost:8000)** in your browser.

---

## Usage

1. **Paste** an Airflow DAG failure log into the text area (or click **LOAD SAMPLE** to try the built-in demo log)
2. Click **⚡ Run Triage Agent**
3. Wait ~3–5 seconds for Claude to analyze the log
4. Review:
   - The **severity strip** at the top (color-coded)
   - The **root cause** card
   - The **Slack** tab — copy-ready alert message
   - The **Email** tab — copy-ready stakeholder email
   - The **Downstream Impact** panel (if any tasks are blocked)

---

## Project Structure

```
flare/
├── main.py           # FastAPI app — serves UI and proxies to Anthropic
├── index.html        # Single-page UI (no build step required)
├── requirements.txt  # Python dependencies
├── .env              # 🔒 Your secret API key (git-ignored)
├── .env.example      # Template for .env
├── .gitignore        # Excludes .env, .venv, __pycache__
└── README.md         # This file
```

---

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `ANTHROPIC_API_KEY` | ✅ Yes | Your Anthropic API key |

---

## Security Notes

- The Anthropic API key is stored in `.env` and **never sent to the browser**.
- The FastAPI backend acts as a secure proxy — the frontend calls `/api/triage`, not Anthropic directly.
- `.env` is included in `.gitignore`. **Never commit your API key.**
- If you've ever had the key hardcoded in source code and pushed to a public repo, rotate it immediately at [console.anthropic.com](https://console.anthropic.com).

---

## Roadmap

- [ ] Real Slack webhook integration (post directly to a channel)
- [ ] Gmail / SMTP integration (send the email with one click)
- [ ] Airflow REST API integration (pull logs automatically from the Airflow UI)
- [ ] Log history & triage audit trail (SQLite)
- [ ] Multi-DAG batch triage
- [ ] Runbook generation per error pattern

---

## Contributing

PRs welcome! Please open an issue first to discuss what you'd like to change.

---

## License

MIT © 2026
