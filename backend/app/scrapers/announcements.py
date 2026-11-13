import httpx
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.models.database import Announcement
from app.core.portfolio import get_portfolio_tickers
import logging

logger = logging.getLogger(__name__)

BSE_API_BASE = "https://api.bseindia.com/BseIndiaAPI/api"

# BSE requires basic browser-ish headers or it throws 403
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.bseindia.com/",
}

# BSE scrip codes for our portfolio
TICKER_TO_BSE_CODE = {
    "TCS.NS": "532540",
    "INFY.NS": "500209",
    "PERSISTENT.NS": "533179",
    "HDFCBANK.NS": "500180",
    "ICICIBANK.NS": "532174",
    "KOTAKBANK.NS": "500247",
    "SUNPHARMA.NS": "524715",
    "DIVISLAB.NS": "532488",
    "TATAMOTORS.NS": "500570",
    "BAJAJ-AUTO.NS": "532977",
    "HINDUNILVR.NS": "500696",
    "TITAN.NS": "500114",
    "RELIANCE.NS": "500325",
    "NTPC.NS": "532555",
    "LT.NS": "500510",
    "BEL.NS": "500049",
    "SRF.NS": "503806",
    "PIDILITIND.NS": "500331",
    "BAJFINANCE.NS": "500034",
    "BHARTIARTL.NS": "532454",
    "ZOMATO.NS": "543320",
    "TRENT.NS": "500251",
    "DIXON.NS": "540699",
    "DEEPAKNTR.NS": "506401",
    "CDSL.NS": "541079",
}


async def fetch_bse_announcements(scrip_code: str, from_date: str, to_date: str) -> list:
    url = f"{BSE_API_BASE}/AnnSubCategoryGetData/w"
    params = {
        "strCat": "-1",
        "strPrevDate": from_date,
        "strScrip": scrip_code,
        "strSearch": "P",
        "strToDate": to_date,
        "strType": "C",
    }
    
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(url, params=params, headers=HEADERS)
            resp.raise_for_status()
            data = resp.json()
            
            if not isinstance(data, dict) or "Table" not in data:
                return []
            
            announcements = []
            for item in data.get("Table", []):
                announcements.append({
                    "headline": item.get("NEWSSUB", ""),
                    "description": item.get("NEWS_DT", ""),
                    "category": item.get("CATEGORYNAME", ""),
                    "filed_at": item.get("NEWS_DT", ""),
                    "attachment_url": item.get("ATTACHMENTNAME", ""),
                    "source": "BSE",
                })
            return announcements
    except Exception as e:
        logger.error(f"BSE API error for scrip {scrip_code}: {e}")
        return []


async def fetch_announcements_for_ticker(ticker: str, days: int = 7) -> list:
    scrip_code = TICKER_TO_BSE_CODE.get(ticker)
    if not scrip_code:
        logger.warning(f"No BSE scrip code mapped for {ticker}")
        return []
    
    to_date = datetime.now().strftime("%d/%m/%Y")
    from_date = (datetime.now() - timedelta(days=days)).strftime("%d/%m/%Y")
    return await fetch_bse_announcements(scrip_code, from_date, to_date)


def parse_announcement_date(date_str: str) -> datetime:
    for fmt in ["%d/%m/%Y %H:%M:%S", "%d-%m-%Y %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%d/%m/%Y"]:
        try:
            return datetime.strptime(date_str.strip(), fmt)
        except (ValueError, AttributeError):
            continue
    return datetime.utcnow()


def store_announcements(db: Session, ticker: str, raw_announcements: list):
    stored = 0
    for ann in raw_announcements:
        headline = ann.get("headline", "").strip()
        if not headline:
            continue
        
        # skip if already saved
        existing = db.query(Announcement).filter_by(
            ticker=ticker, headline=headline
        ).first()
        if existing:
            continue
        
        filed_at = parse_announcement_date(ann.get("filed_at", ""))
        filing_url = ann.get("attachment_url", "")
        if filing_url and not filing_url.startswith("http"):
            filing_url = f"https://www.bseindia.com/xml-data/corpfiling/AttachLive/{filing_url}"
        
        db.add(Announcement(
            ticker=ticker,
            source=ann.get("source", "BSE"),
            category="unclassified",
            headline=headline,
            description=ann.get("description", ""),
            filing_url=filing_url,
            filed_at=filed_at,
            priority="low",
        ))
        stored += 1
    
    db.commit()
    return stored


async def refresh_all_announcements(db: Session, days: int = 7):
    tickers = get_portfolio_tickers()
    total = 0
    
    for ticker in tickers:
        raw = await fetch_announcements_for_ticker(ticker, days=days)
        count = store_announcements(db, ticker, raw)
        total += count
    return total


def get_recent_announcements(db: Session, tickers: list = None, hours: int = 24,
                              categories: list = None, priority: str = None):
    cutoff = datetime.utcnow() - timedelta(hours=hours)
    query = db.query(Announcement).filter(Announcement.filed_at >= cutoff)
    
    if tickers:
        query = query.filter(Announcement.ticker.in_(tickers))
    if categories:
        query = query.filter(Announcement.category.in_(categories))
    if priority:
        query = query.filter(Announcement.priority == priority)
    
    return query.order_by(Announcement.filed_at.desc()).all()
