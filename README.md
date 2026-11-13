# FINN

Investment research tool. Tracks 20 NSE-listed companies, surfaces what matters, buries what doesn't.

Two modes: **push** (it tells you) and **pull** (you ask it).

## Setup

```bash
# backend
cd backend
pip install -r requirements.txt
cp .env.example .env   # add GEMINI_API_KEY if you have one
python -m uvicorn main:app --reload --port 8000

# frontend
cd frontend
npm install
npm run dev
```

Hit `http://localhost:3000` on your phone (use your machine's local IP if on the same wifi).

## What it does

**Push side** — every N hours, pulls corporate filings from BSE, price/volume from yfinance, classifies announcements by materiality, and shows you a digest. High-priority stuff (results, M&A, management exits) floats to the top. Routine compliance junk gets collapsed. Price and volume anomalies generate alerts with configurable thresholds.

**Pull side** — pick any NSE ticker and run one of eight analysis types against its audited filings (screener.in data). Narrative-vs-numbers is the one I'd demo first — it compares what management said on concalls vs what the numbers actually did.

## Stack

- Next.js 14 / Tailwind for the frontend (dark theme, mobile-first)
- FastAPI / SQLAlchemy / SQLite for the backend
- yfinance for EOD prices, BSE API for announcements, screener.in for fundamentals
- Gemini Flash for cheap bulk tasks (classification, extraction), Gemini Pro for reasoning (analysis, bull/bear)

## Structure

```
backend/
  app/
    api/          routes
    core/         config, db, portfolio list
    models/       sqlalchemy tables
    scrapers/     BSE announcement fetcher
    services/     price pipeline, LLM calls, screener scraper
  main.py

frontend/
  src/
    app/          pages
    components/   PushView, PullView, PortfolioView, SettingsView
    lib/          api client, formatting helpers
```
