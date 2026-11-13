from datetime import datetime, timedelta
import json
from sqlalchemy.orm import Session
from app.models.database import Announcement, Alert

# Seed filings to bootstrap the UI before live scrapers run
SAMPLE_ANNOUNCEMENTS = [
    {
        "ticker": "TCS.NS",
        "source": "BSE",
        "category": "results",
        "priority": "high",
        "headline": "Audited Financial Results for Q2 FY26 ended September 30, 2026",
        "description": "Board approved Q2 consolidated financial results. Revenue at ₹64,259 Cr, Operating Margin at 25.5%. Interim dividend of ₹10 per share declared.",
        "summary": "Revenue up 7.6% YoY to ₹64,259 Cr. EBITDA margin steady at 25.5% (+20 bps QoQ). Interim dividend ₹10/sh.",
        "filing_url": "https://www.bseindia.com/xml-data/corpfiling/AttachLive/ad42e748-d73c-4c79-8c52-bcf1b1399bc1.pdf",
        "hours_ago": 3,
        "enrichment": json.dumps({
            "type": "results",
            "quarter": "Q2 FY26",
            "metrics": {
                "revenue": {"val": "₹64,259 Cr", "qoq": "+2.2%", "yoy": "+7.6%"},
                "ebitda": {"val": "₹16,365 Cr", "qoq": "+3.1%", "yoy": "+6.8%", "margin": "25.5%"},
                "pbt": {"val": "₹16,012 Cr", "qoq": "+2.8%", "yoy": "+7.1%"},
                "pat": {"val": "₹11,909 Cr", "qoq": "+2.5%", "yoy": "+5.0%"}
            },
            "verdict": "Decent quarter, BFSI bouncing back (+3.1% CC). TCV strong at $8.6B though pipeline conversion pace matters now."
        })
    },
    {
        "ticker": "KOTAKBANK.NS",
        "source": "BSE",
        "category": "management_change",
        "priority": "high",
        "headline": "Appointment of Group Chief Financial Officer (CFO)",
        "description": "The Board has approved appointment of Mr. Devang Gheewalla as Group CFO with immediate effect succeeding Mr. Jaimin Bhatt upon retirement.",
        "summary": "Devang Gheewalla appointed Group CFO. 20-yr Kotak veteran with leadership across Treasury & Wholesale credit.",
        "filing_url": "https://www.bseindia.com/stock-share-price/kotak-mahindra-bank-ltd/kotakbank/500247/corp-announcements/",
        "hours_ago": 7,
        "enrichment": json.dumps({
            "type": "management_change",
            "person": "Devang Gheewalla",
            "new_role": "Group Chief Financial Officer",
            "prior_role": "Head of Treasury & Balance Sheet Management",
            "pedigree": "20+ years inside Kotak. Handled ALM and treasury during credit crunches.",
            "predecessor": "Jaimin Bhatt (retiring after 30 years)",
            "verdict": "Zero surprise here. Internal promotion, keeps the conservative treasury culture intact."
        })
    },
    {
        "ticker": "RELIANCE.NS",
        "source": "BSE",
        "category": "m_and_a",
        "priority": "high",
        "headline": "Strategic Joint Venture between Reliance Industries and Disney India Completes Regulatory Approvals",
        "description": "NCLT and CCI clear creation of $8.5B media giant combining JioCinema and Disney+ Hotstar with Reliance holding controlling 56% stake.",
        "summary": "NCLT & CCI clear $8.5B Reliance-Disney merger. Reliance controls 56% with 100+ TV channels & dual OTT domination.",
        "filing_url": "https://www.bseindia.com/stock-share-price/reliance-industries-ltd/reliance/500325/corp-announcements/",
        "hours_ago": 11,
        "enrichment": json.dumps({
            "type": "m_and_a",
            "deal_type": "Joint Venture & Media Merger",
            "valuation": "$8.5 Billion",
            "stake": "56% Reliance Group (16% RIL, 40% Viacom18), 37% Disney",
            "verdict": "Effective monopoly on Indian cricket rights (IPL + ICC). OTT cash burn should drop sharply as bidding wars end."
        })
    },
    {
        "ticker": "LT.NS",
        "source": "BSE",
        "category": "capex",
        "priority": "medium",
        "headline": "L&T Hydrocarbon Onshore Business Secures Mega Order in Middle East valued at ₹15,000+ Cr",
        "description": "Letter of Intent received for EPC of gas processing plant in UAE. Execution timeline 42 months.",
        "summary": "Secured ₹15,000+ Cr EPC order for gas processing plant in UAE. Order book extends beyond 3.2x trailing revenues.",
        "filing_url": "https://www.bseindia.com/stock-share-price/larsen-toubro-ltd/lt/500510/corp-announcements/",
        "hours_ago": 14,
        "enrichment": json.dumps({
            "type": "order_win",
            "value": "₹15,000+ Cr",
            "geography": "Middle East",
            "margin_profile": "Est ~9-10% EBITDA"
        })
    },
    {
        "ticker": "TATAMOTORS.NS",
        "source": "BSE",
        "category": "results",
        "priority": "high",
        "headline": "Q2 FY26 Earnings Conference Call Transcript and Presentation",
        "description": "Transcript of concall held on Nov 10, 2026. Management discussion on JLR EBIT margin guidance and CV demerger roadmap.",
        "summary": "Concall transcript released: JLR EBIT margin maintained at 8.5% despite aluminum supply disruption. CV demerger on track for Q1FY27.",
        "filing_url": "https://www.bseindia.com/stock-share-price/tata-motors-ltd/tatamotors/500570/corp-announcements/",
        "hours_ago": 18,
        "enrichment": json.dumps({
            "type": "transcript",
            "highlights": "JLR order book ~145k units with 68% Range Rover/Defender mix. Domestic EV share 62%."
        })
    },
    {
        "ticker": "BAJFINANCE.NS",
        "source": "BSE",
        "category": "fund_raise",
        "priority": "medium",
        "headline": "Allotment of Non-Convertible Debentures (NCDs) aggregating ₹2,500 Crores",
        "description": "Private placement of unsecured redeemable NCDs coupon 7.78% p.a. rated CRISIL AAA/Stable.",
        "summary": "Raised ₹2,500 Cr via 3-year NCDs at 7.78% coupon. Cost of funds remains well-anchored.",
        "filing_url": "https://www.bseindia.com",
        "hours_ago": 22,
        "enrichment": None
    },
    {
        "ticker": "INFY.NS",
        "source": "BSE",
        "category": "dividend",
        "priority": "medium",
        "headline": "Record date for Interim Dividend of ₹21 per equity share",
        "description": "November 21, 2026 fixed as record date for determining shareholders entitled to receive interim dividend.",
        "summary": "Record date fixed for ₹21/share interim dividend. Dividend yield 2.1%.",
        "filing_url": "https://www.bseindia.com",
        "hours_ago": 26,
        "enrichment": None
    },
    {
        "ticker": "HDFCBANK.NS",
        "source": "BSE",
        "category": "unclassified",
        "priority": "low",
        "headline": "Intimation under Regulation 30 - Schedule of Institutional Investor Meeting",
        "description": "Bank officials to meet GIC Singapore on Nov 14 in Mumbai.",
        "summary": "Routine institutional investor interaction schedule with GIC Singapore.",
        "filing_url": "https://www.bseindia.com",
        "hours_ago": 30,
        "enrichment": None
    },
    {
        "ticker": "SUNPHARMA.NS",
        "source": "BSE",
        "category": "unclassified",
        "priority": "low",
        "headline": "Compliance Certificate under Regulation 74(5) of SEBI DP Regulations",
        "description": "Dematerialization certificate for period ended September 30, 2026 received from Link Intime.",
        "summary": "Quarterly depository participant compliance certificate.",
        "filing_url": "https://www.bseindia.com",
        "hours_ago": 34,
        "enrichment": None
    }
]

SAMPLE_ALERTS = [
    {
        "ticker": "TATAMOTORS.NS",
        "alert_type": "price_spike",
        "title": "Tata Motors surged +4.8%",
        "body": "Closed at ₹1,024.50, up 4.8% following upbeat JLR guidance and strong wholesale numbers.",
        "severity": "critical",
        "data_json": json.dumps({"close": 1024.50, "prev_close": 977.50, "change_pct": 4.8}),
        "hours_ago": 4
    },
    {
        "ticker": "PERSISTENT.NS",
        "alert_type": "volume_spike",
        "title": "Persistent Systems volume 3.4× above average",
        "body": "Traded 1.48M shares vs 20-day avg of 435K. Institutional block trade suspected near ₹5,450.",
        "severity": "warning",
        "data_json": json.dumps({"volume": 1480000, "volume_ratio": 3.4}),
        "hours_ago": 6
    },
    {
        "ticker": "SRF.NS",
        "alert_type": "price_spike",
        "title": "SRF dropped -3.2%",
        "body": "Chemicals export realizations under margin pressure; closed at ₹2,180.00 (-3.2%).",
        "severity": "warning",
        "data_json": json.dumps({"close": 2180.00, "prev_close": 2252.00, "change_pct": -3.2}),
        "hours_ago": 16
    }
]

def seed_rich_demo_data(db: Session):
    now = datetime.utcnow()
    
    for item in SAMPLE_ANNOUNCEMENTS:
        existing = db.query(Announcement).filter_by(
            ticker=item["ticker"], headline=item["headline"]
        ).first()
        if existing:
            existing.filed_at = now - timedelta(hours=item["hours_ago"])
            existing.enrichment = item["enrichment"]
            existing.summary = item["summary"]
            existing.priority = item["priority"]
            existing.category = item["category"]
        else:
            db.add(Announcement(
                ticker=item["ticker"],
                source=item["source"],
                category=item["category"],
                headline=item["headline"],
                description=item["description"],
                summary=item["summary"],
                priority=item["priority"],
                filing_url=item["filing_url"],
                filed_at=now - timedelta(hours=item["hours_ago"]),
                enrichment=item["enrichment"],
                created_at=now
            ))
            
    for item in SAMPLE_ALERTS:
        existing = db.query(Alert).filter_by(
            ticker=item["ticker"], title=item["title"]
        ).first()
        if existing:
            existing.triggered_at = now - timedelta(hours=item["hours_ago"])
        else:
            db.add(Alert(
                ticker=item["ticker"],
                alert_type=item["alert_type"],
                title=item["title"],
                body=item["body"],
                severity=item["severity"],
                data_json=item["data_json"],
                is_read=False,
                triggered_at=now - timedelta(hours=item["hours_ago"])
            ))
            
    db.commit()
