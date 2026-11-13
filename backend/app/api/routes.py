from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.price_service import (
    refresh_all_prices, get_latest_prices, get_price_history
)
from app.scrapers.announcements import (
    refresh_all_announcements, get_recent_announcements
)
from app.services.llm_service import (
    classify_batch, deep_company_analysis, generate_digest_summary,
    enrich_management_change, analyze_quarterly_results
)
from app.models.database import Alert, Announcement, Company, PriceData, UserSettings
from app.core.portfolio import PORTFOLIO, ALL_COMPANIES, HIGH_PRIORITY, MEDIUM_PRIORITY
from app.services.screener_service import fetch_screener_data
from datetime import datetime, timedelta
from typing import Optional
import json

router = APIRouter()


# health
@router.get("/health")
def health():
    return {"status": "alive", "service": "FINN", "timestamp": datetime.utcnow().isoformat()}


# portfolio overview
@router.get("/portfolio")
def get_portfolio(db: Session = Depends(get_db)):
    prices = get_latest_prices(db, [c["ticker"] for c in PORTFOLIO])
    
    result = []
    for company in PORTFOLIO:
        price_data = next((p for p in prices if p.ticker == company["ticker"]), None)
        result.append({
            "ticker": company["ticker"],
            "name": company["name"],
            "sector": company["sector"],
            "close": price_data.close if price_data else None,
            "change_pct": price_data.change_pct if price_data else None,
            "volume": price_data.volume if price_data else None,
            "volume_ratio": price_data.volume_ratio if price_data else None,
            "date": str(price_data.date) if price_data else None,
        })
    
    return {"portfolio": result, "count": len(result)}


@router.get("/portfolio/{ticker}/history")
def get_ticker_history(ticker: str, days: int = Query(90, ge=7, le=365),
                       db: Session = Depends(get_db)):
    history = get_price_history(db, ticker, days=days)
    if not history:
        raise HTTPException(404, f"No price data for {ticker}")
    
    return {
        "ticker": ticker,
        "days": days,
        "data": [
            {
                "date": str(h.date),
                "open": h.open,
                "high": h.high,
                "low": h.low,
                "close": h.close,
                "volume": h.volume,
                "change_pct": h.change_pct,
                "volume_ratio": h.volume_ratio,
            }
            for h in history
        ]
    }


# push digest
@router.get("/push/digest")
def get_digest(hours: int = Query(24, ge=1, le=168), db: Session = Depends(get_db)):
    tickers = [c["ticker"] for c in PORTFOLIO]
    announcements = get_recent_announcements(db, tickers=tickers, hours=hours)
    
    # bucket by priority
    high = [a for a in announcements if a.priority == "high"]
    medium = [a for a in announcements if a.priority == "medium"]
    low = [a for a in announcements if a.priority == "low"]
    
    cutoff = datetime.utcnow() - timedelta(hours=hours)
    alerts = (
        db.query(Alert)
        .filter(Alert.triggered_at >= cutoff, Alert.ticker.in_(tickers))
        .order_by(Alert.triggered_at.desc())
        .all()
    )
    
    def ann_to_dict(a):
        company = next((c for c in PORTFOLIO if c["ticker"] == a.ticker), {})
        return {
            "id": a.id,
            "ticker": a.ticker,
            "company": company.get("name", a.ticker),
            "sector": company.get("sector", ""),
            "category": a.category,
            "headline": a.headline,
            "summary": a.summary or a.headline[:100],
            "priority": a.priority,
            "filing_url": a.filing_url,
            "filed_at": a.filed_at.isoformat() if a.filed_at else None,
            "enrichment": a.enrichment,
        }
    
    def alert_to_dict(a):
        company = next((c for c in ALL_COMPANIES if c["ticker"] == a.ticker), {})
        return {
            "id": a.id,
            "ticker": a.ticker,
            "company": company.get("name", a.ticker),
            "alert_type": a.alert_type,
            "title": a.title,
            "body": a.body,
            "severity": a.severity,
            "data": json.loads(a.data_json) if a.data_json else {},
            "triggered_at": a.triggered_at.isoformat() if a.triggered_at else None,
            "is_read": a.is_read,
        }
    
    return {
        "window_hours": hours,
        "generated_at": datetime.utcnow().isoformat(),
        "critical": [ann_to_dict(a) for a in high],
        "notable": [ann_to_dict(a) for a in medium],
        "routine": [ann_to_dict(a) for a in low],
        "price_alerts": [alert_to_dict(a) for a in alerts],
        "counts": {
            "critical": len(high),
            "notable": len(medium),
            "routine": len(low),
            "price_alerts": len(alerts),
        }
    }


# push alerts
@router.get("/push/alerts")
def get_alerts(unread_only: bool = Query(True), limit: int = Query(50),
               db: Session = Depends(get_db)):
    query = db.query(Alert).order_by(Alert.triggered_at.desc())
    if unread_only:
        query = query.filter(Alert.is_read == False)
    alerts = query.limit(limit).all()
    
    return {
        "alerts": [
            {
                "id": a.id,
                "ticker": a.ticker,
                "alert_type": a.alert_type,
                "title": a.title,
                "body": a.body,
                "severity": a.severity,
                "data": json.loads(a.data_json) if a.data_json else {},
                "triggered_at": a.triggered_at.isoformat() if a.triggered_at else None,
                "is_read": a.is_read,
            }
            for a in alerts
        ],
        "count": len(alerts),
    }


@router.post("/push/alerts/{alert_id}/read")
def mark_alert_read(alert_id: int, db: Session = Depends(get_db)):
    alert = db.query(Alert).filter_by(id=alert_id).first()
    if not alert:
        raise HTTPException(404, "Alert not found")
    alert.is_read = True
    db.commit()
    return {"status": "ok"}


# AI briefing
@router.get("/push/briefing")
def get_ai_briefing(hours: int = Query(24, ge=1, le=168), db: Session = Depends(get_db)):
    tickers = [c["ticker"] for c in PORTFOLIO]
    announcements = get_recent_announcements(db, tickers=tickers, hours=hours)
    
    cutoff = datetime.utcnow() - timedelta(hours=hours)
    alerts = (
        db.query(Alert)
        .filter(Alert.triggered_at >= cutoff)
        .all()
    )
    
    ann_dicts = [{"ticker": a.ticker, "headline": a.headline, "summary": a.summary,
                  "priority": a.priority, "category": a.category} for a in announcements]
    alert_dicts = [{"title": a.title, "body": a.body} for a in alerts]
    
    briefing = generate_digest_summary(ann_dicts, alert_dicts)
    return {
        "window_hours": hours,
        "generated_at": datetime.utcnow().isoformat(),
        "briefing": briefing,
        "announcement_count": len(announcements),
        "alert_count": len(alerts),
    }


# pull: deep company research
@router.get("/pull/research/{ticker}")
def research_company(ticker: str,
                     analysis: str = Query("business_snapshot",
                         enum=["business_snapshot", "financial_snapshot", "trajectory",
                               "balance_sheet", "cash_quality", "narrative_vs_numbers",
                               "guidance", "bull_bear"]),
                     db: Session = Depends(get_db)):
    company = db.query(Company).filter_by(ticker=ticker).first()
    if not company:
        company_data = next((c for c in ALL_COMPANIES if c["ticker"] == ticker), None)
        company_name = company_data["name"] if company_data else ticker.replace(".NS", "")
    else:
        company_name = company.name
    
    # pull primary fundamentals from Screener
    primary_data = fetch_screener_data(ticker)
    
    source_lines = [
        f"COMPANY: {primary_data.get('name', company_name)} ({ticker})",
        f"ABOUT: {primary_data.get('about', '')}",
        "KEY AUDITED RATIOS:",
    ]
    for k, v in primary_data.get("ratios", {}).items():
        source_lines.append(f"  {k}: {v}")
    
    source_lines.append("\nRECENT QUARTERLY RESULTS (Audited exchange filings):")
    for q in primary_data.get("quarters", []):
        source_lines.append(f"  [{q.get('quarter')}] Sales: ₹{q.get('Sales')}Cr | EBITDA: ₹{q.get('Operating Profit')}Cr ({q.get('OPM %')}) | PBT: ₹{q.get('Profit before tax')}Cr | PAT: ₹{q.get('Net Profit')}Cr")
        
    source_lines.append("\nPRIMARY DISCLOSURES & CONCALL TRANSCRIPTS:")
    for d in primary_data.get("documents", []):
        source_lines.append(f"  - {d.get('title')}: {d.get('url')}")
        
    source_text = "\n".join(source_lines)
    
    result = deep_company_analysis(company_name, ticker, analysis, source_text=source_text, primary_data=primary_data)
    
    return {
        "ticker": ticker,
        "company": company_name,
        "analysis_type": analysis,
        "generated_at": datetime.utcnow().isoformat(),
        "content": result,
        "source": "primary_filings",
        "primary_data": primary_data,
        "model_used": "gemini-1.5-pro",
    }


# pull: chat
@router.post("/pull/chat")
def chat_with_finn(request: dict, db: Session = Depends(get_db)):
    from app.services.llm_service import _call_gemini, PRO_MODEL
    from app.core.config import settings
    
    user_message = request.get("message", "").strip()
    if not user_message:
        raise HTTPException(400, "Message required")
        
    matched_ticker = None
    user_upper = user_message.upper()
    for c in ALL_COMPANIES:
        sym = c["ticker"].replace(".NS", "")
        if sym in user_upper or c["name"].lower() in user_message.lower():
            matched_ticker = c["ticker"]
            break
            
    fundamentals_ctx = ""
    if matched_ticker:
        p_data = fetch_screener_data(matched_ticker)
        q_latest = p_data.get("quarters", [])[-1] if p_data.get("quarters") else {}
        fundamentals_ctx = f"""
PRIMARY DATA FOR REFERENCED COMPANY ({p_data.get('name', matched_ticker)}):
Ratios: {p_data.get('ratios', {})}
Latest Quarter ({q_latest.get('quarter', 'Q2')}): Sales ₹{q_latest.get('Sales', 'N/A')}Cr, OPM {q_latest.get('OPM %', 'N/A')}, PAT ₹{q_latest.get('Net Profit', 'N/A')}Cr
Documents: {[d.get('title') for d in p_data.get('documents', [])[:3]]}
"""
    
    context = f"""You are FINN, a sharp financial investment agent. You work for an investor tracking Indian listed companies.

PORTFOLIO: {', '.join(c['name'] + ' (' + c['ticker'] + ')' for c in PORTFOLIO)}

{fundamentals_ctx}

USER QUESTION: {user_message}

RULES:
- Answer like a senior analyst briefing a portfolio manager. Dense, specific, no filler.
- Ground analysis strictly in primary data and exchange disclosures.
- Use numbers and specifics.
- Never say 'as an AI'. Speak directly with high-conviction judgment."""

    response = ""
    if settings.gemini_api_key:
        response = _call_gemini(context, model_name=PRO_MODEL, temperature=0.3)
        
    if not response:
        if matched_ticker:
            p_data = fetch_screener_data(matched_ticker)
            q_latest = p_data.get("quarters", [])[-1] if p_data.get("quarters") else {}
            ratios = p_data.get("ratios", {})
            response = (
                f"**{p_data.get('name', matched_ticker)} ({matched_ticker}) Overview:**\n\n"
                f"• **Valuation:** Market Cap {ratios.get('Market Cap', 'N/A')} at {ratios.get('Stock P/E', 'N/A')}x P/E.\n"
                f"• **Latest Quarter ({q_latest.get('quarter', 'Latest')}):** Revenue ₹{q_latest.get('Sales', 'N/A')} Cr ({q_latest.get('YoY Sales growth', 'N/A')} YoY), "
                f"Operating Profit ₹{q_latest.get('Operating Profit', 'N/A')} Cr with margin at {q_latest.get('OPM %', 'N/A')}, and PAT of ₹{q_latest.get('Net Profit', 'N/A')} Cr.\n"
                f"• **Return & Solvency:** ROCE is {ratios.get('ROCE', 'N/A')}, ROE is {ratios.get('ROE', 'N/A')}, with Debt-to-Equity at {ratios.get('Debt to equity', 'N/A')}.\n\n"
                f"Grounded in audited disclosures and earnings transcripts from Screener & BSE."
            )
        else:
            response = (
                f"Tracking 20 high-conviction portfolio positions across IT, Banking, Industrials, Auto, and Pharma. "
                f"You can ask me to run an on-demand analysis on any ticker (e.g. TCS, Reliance, Trent) or switch to the Structured tab to inspect Narrative vs. Numbers, Balance Sheet, or Cash Quality."
            )
    
    return {
        "response": response,
        "generated_at": datetime.utcnow().isoformat(),
    }


# manual triggers
@router.post("/data/refresh/prices")
def refresh_prices(db: Session = Depends(get_db)):
    alerts = refresh_all_prices(db)
    return {"status": "done", "alerts_generated": len(alerts)}


@router.post("/data/refresh/announcements")
async def refresh_announcements(days: int = Query(7, ge=1, le=30),
                                 db: Session = Depends(get_db)):
    count = await refresh_all_announcements(db, days=days)
    return {"status": "done", "new_announcements": count}


@router.post("/data/classify")
def classify_announcements(limit: int = Query(50), db: Session = Depends(get_db)):
    count = classify_batch(db, limit=limit)
    return {"status": "done", "classified": count}


# settings
@router.get("/settings")
def get_settings(db: Session = Depends(get_db)):
    s = db.query(UserSettings).first()
    if not s:
        s = UserSettings()
        db.add(s)
        db.commit()
        db.refresh(s)
    return {
        "volume_threshold": s.volume_threshold,
        "price_change_threshold": s.price_change_threshold,
        "digest_window_hours": s.digest_window_hours,
        "alert_categories": s.alert_categories.split(",") if s.alert_categories else [],
    }


@router.put("/settings")
def update_settings(request: dict, db: Session = Depends(get_db)):
    s = db.query(UserSettings).first()
    if not s:
        s = UserSettings()
        db.add(s)
    
    if "volume_threshold" in request:
        s.volume_threshold = request["volume_threshold"]
    if "price_change_threshold" in request:
        s.price_change_threshold = request["price_change_threshold"]
    if "digest_window_hours" in request:
        s.digest_window_hours = request["digest_window_hours"]
    if "alert_categories" in request:
        s.alert_categories = ",".join(request["alert_categories"])
    
    db.commit()
    return {"status": "updated"}
