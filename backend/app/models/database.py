import sqlalchemy as sa
from sqlalchemy.orm import declarative_base
from datetime import datetime

Base = declarative_base()


class Company(Base):
    __tablename__ = "companies"

    id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)
    ticker = sa.Column(sa.String(30), unique=True, nullable=False, index=True)
    name = sa.Column(sa.String(100), nullable=False)
    sector = sa.Column(sa.String(50))
    is_portfolio = sa.Column(sa.Boolean, default=False)
    market_cap = sa.Column(sa.Float, nullable=True)
    created_at = sa.Column(sa.DateTime, default=datetime.utcnow)


class PriceData(Base):
    __tablename__ = "price_data"

    id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)
    ticker = sa.Column(sa.String(30), sa.ForeignKey("companies.ticker"), nullable=False, index=True)
    date = sa.Column(sa.Date, nullable=False, index=True)
    open = sa.Column(sa.Float)
    high = sa.Column(sa.Float)
    low = sa.Column(sa.Float)
    close = sa.Column(sa.Float)
    volume = sa.Column(sa.BigInteger)
    prev_close = sa.Column(sa.Float, nullable=True)
    change_pct = sa.Column(sa.Float, nullable=True)
    volume_ratio = sa.Column(sa.Float, nullable=True)  # vs 20d avg

    __table_args__ = (
        sa.UniqueConstraint("ticker", "date", name="uq_ticker_date"),
    )


class Announcement(Base):
    __tablename__ = "announcements"

    id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)
    ticker = sa.Column(sa.String(30), sa.ForeignKey("companies.ticker"), nullable=False, index=True)
    source = sa.Column(sa.String(10))
    category = sa.Column(sa.String(30), index=True)
    headline = sa.Column(sa.Text, nullable=False)
    description = sa.Column(sa.Text, nullable=True)
    summary = sa.Column(sa.Text, nullable=True)
    priority = sa.Column(sa.String(10), default="low")
    filing_url = sa.Column(sa.String(500), nullable=True)
    filed_at = sa.Column(sa.DateTime, nullable=False, index=True)
    enrichment = sa.Column(sa.Text, nullable=True)  # json blob
    created_at = sa.Column(sa.DateTime, default=datetime.utcnow)


class Alert(Base):
    __tablename__ = "alerts"

    id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)
    ticker = sa.Column(sa.String(30), nullable=False, index=True)
    alert_type = sa.Column(sa.String(30))
    title = sa.Column(sa.String(200))
    body = sa.Column(sa.Text)
    severity = sa.Column(sa.String(10))
    data_json = sa.Column(sa.Text, nullable=True)
    is_read = sa.Column(sa.Boolean, default=False)
    triggered_at = sa.Column(sa.DateTime, default=datetime.utcnow)


class UserSettings(Base):
    __tablename__ = "user_settings"

    id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)
    volume_threshold = sa.Column(sa.Float, default=2.0)
    price_change_threshold = sa.Column(sa.Float, default=3.0)
    digest_window_hours = sa.Column(sa.Integer, default=24)
    alert_categories = sa.Column(sa.Text, default="results,m_and_a,management_change,litigation,fund_raise")
