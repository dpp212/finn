import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.models.database import PriceData, Company, Alert
from app.core.portfolio import PORTFOLIO, ADHOC_COMPANIES, ALL_COMPANIES
from app.core.config import settings
import logging
import json

logger = logging.getLogger(__name__)

VOLUME_WINDOW = 20


def seed_companies(db: Session):
    for c in PORTFOLIO:
        existing = db.query(Company).filter_by(ticker=c["ticker"]).first()
        if not existing:
            db.add(Company(ticker=c["ticker"], name=c["name"], sector=c["sector"], is_portfolio=True))
    for c in ADHOC_COMPANIES:
        existing = db.query(Company).filter_by(ticker=c["ticker"]).first()
        if not existing:
            db.add(Company(ticker=c["ticker"], name=c["name"], sector=c["sector"], is_portfolio=False))
    db.commit()


def fetch_prices_for_ticker(ticker: str, period: str = "3mo") -> pd.DataFrame:
    try:
        stock = yf.Ticker(ticker)
        df = stock.history(period=period, interval="1d")
        if df.empty:
            logger.warning(f"no data returned for {ticker}")
            return pd.DataFrame()
        df = df.reset_index()
        df["ticker"] = ticker
        return df
    except Exception as e:
        logger.error(f"yfinance error for {ticker}: {e}")
        return pd.DataFrame()


def compute_signals(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    
    df = df.sort_values("Date").reset_index(drop=True)
    df["prev_close"] = df["Close"].shift(1)
    df["change_pct"] = ((df["Close"] - df["prev_close"]) / df["prev_close"] * 100).round(2)
    # rolling 20d vol avg, needs at least 5 days of data
    df["vol_avg_20"] = df["Volume"].rolling(window=VOLUME_WINDOW, min_periods=5).mean()
    df["volume_ratio"] = (df["Volume"] / df["vol_avg_20"]).round(2)
    return df


def store_prices(db: Session, ticker: str, df: pd.DataFrame):
    if df.empty:
        return
    
    for _, row in df.iterrows():
        date_val = row["Date"].date() if hasattr(row["Date"], "date") else row["Date"]
        existing = db.query(PriceData).filter_by(ticker=ticker, date=date_val).first()
        
        if existing:
            existing.open = row.get("Open")
            existing.high = row.get("High")
            existing.low = row.get("Low")
            existing.close = row.get("Close")
            existing.volume = int(row.get("Volume", 0))
            existing.prev_close = row.get("prev_close")
            existing.change_pct = row.get("change_pct")
            existing.volume_ratio = row.get("volume_ratio")
        else:
            db.add(PriceData(
                ticker=ticker,
                date=date_val,
                open=row.get("Open"),
                high=row.get("High"),
                low=row.get("Low"),
                close=row.get("Close"),
                volume=int(row.get("Volume", 0)),
                prev_close=row.get("prev_close"),
                change_pct=row.get("change_pct"),
                volume_ratio=row.get("volume_ratio"),
            ))
    db.commit()


def check_price_alerts(db: Session, ticker: str, df: pd.DataFrame,
                       price_threshold: float = None, volume_threshold: float = None):
    if df.empty or len(df) < 2:
        return []
    
    price_threshold = price_threshold or settings.default_price_change_pct
    volume_threshold = volume_threshold or settings.default_volume_multiplier
    
    latest = df.iloc[-1]
    alerts = []
    
    # price move check
    change = latest.get("change_pct")
    if change is not None and abs(change) >= price_threshold:
        direction = "surged" if change > 0 else "dropped"
        company = db.query(Company).filter_by(ticker=ticker).first()
        name = company.name if company else ticker
        
        alert = Alert(
            ticker=ticker,
            alert_type="price_spike",
            title=f"{name} {direction} {abs(change):.1f}%",
            body=f"Closed at ₹{latest['Close']:.2f}, {direction} {abs(change):.1f}% from previous close of ₹{latest.get('prev_close', 0):.2f}.",
            severity="critical" if abs(change) >= price_threshold * 1.5 else "warning",
            data_json=json.dumps({
                "close": float(latest["Close"]),
                "prev_close": float(latest.get("prev_close", 0)),
                "change_pct": float(change),
            }),
            triggered_at=datetime.utcnow(),
        )
        db.add(alert)
        alerts.append(alert)
    
    # volume spike check
    vol_ratio = latest.get("volume_ratio")
    if vol_ratio is not None and vol_ratio >= volume_threshold:
        company = db.query(Company).filter_by(ticker=ticker).first()
        name = company.name if company else ticker
        
        alert = Alert(
            ticker=ticker,
            alert_type="volume_spike",
            title=f"{name} volume {vol_ratio:.1f}× above average",
            body=f"Traded {int(latest['Volume']):,} shares — {vol_ratio:.1f}× the 20-day average.",
            severity="warning",
            data_json=json.dumps({
                "volume": int(latest["Volume"]),
                "volume_ratio": float(vol_ratio),
            }),
            triggered_at=datetime.utcnow(),
        )
        db.add(alert)
        alerts.append(alert)
    
    if alerts:
        db.commit()
    return alerts


def refresh_all_prices(db: Session, period: str = "3mo"):
    from app.core.portfolio import get_portfolio_tickers
    
    tickers = get_portfolio_tickers()
    total_alerts = []
    
    for ticker in tickers:
        logger.info(f"fetching prices for {ticker}...")
        df = fetch_prices_for_ticker(ticker, period=period)
        df = compute_signals(df)
        store_prices(db, ticker, df)
        alerts = check_price_alerts(db, ticker, df)
        total_alerts.extend(alerts)
    
    return total_alerts


def get_latest_prices(db: Session, tickers: list = None):
    from sqlalchemy import func
    
    query = db.query(PriceData)
    if tickers:
        query = query.filter(PriceData.ticker.in_(tickers))
    
    subq = (
        db.query(PriceData.ticker, func.max(PriceData.date).label("max_date"))
        .group_by(PriceData.ticker)
    )
    if tickers:
        subq = subq.filter(PriceData.ticker.in_(tickers))
    subq = subq.subquery()
    
    return (
        query.join(subq, (PriceData.ticker == subq.c.ticker) & (PriceData.date == subq.c.max_date))
        .all()
    )


def get_price_history(db: Session, ticker: str, days: int = 90):
    cutoff = datetime.utcnow().date() - timedelta(days=days)
    return (
        db.query(PriceData)
        .filter(PriceData.ticker == ticker, PriceData.date >= cutoff)
        .order_by(PriceData.date.asc())
        .all()
    )
