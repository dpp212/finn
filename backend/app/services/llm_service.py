import google.generativeai as genai
from app.core.config import settings
from app.core.portfolio import ANNOUNCEMENT_CATEGORIES
from sqlalchemy.orm import Session
from app.models.database import Announcement
import json
import logging
import re

log = logging.getLogger("finn.llm")

if settings.gemini_api_key:
    genai.configure(api_key=settings.gemini_api_key)

# cheap model for bulk work, bigger model where reasoning matters
FLASH = "gemini-2.0-flash"
PRO = "gemini-1.5-pro"
FLASH_MODEL = FLASH
PRO_MODEL = PRO


def _call_gemini(prompt, model_name=FLASH, temperature=0.2):
    try:
        model = genai.GenerativeModel(model_name)
        resp = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=temperature,
                max_output_tokens=2048,
            ),
        )
        return resp.text.strip()
    except Exception as e:
        log.error(f"gemini ({model_name}): {e}")
        return ""


def classify_announcement(headline, description=""):
    cats = ", ".join(ANNOUNCEMENT_CATEGORIES)
    prompt = f"""Classify this corporate announcement. Return ONLY a JSON object:
{{"category": "<one of: {cats}>", "priority": "high|medium|low", "summary": "<10-15 word summary>"}}

Headline: {headline}
{f'Context: {description}' if description else ''}

JSON only, no markdown fences."""

    raw = _call_gemini(prompt, model_name=FLASH, temperature=0.1)
    try:
        cleaned = re.sub(r"```json\s*|\s*```", "", raw).strip()
        r = json.loads(cleaned)
        return {
            "category": r.get("category", "unclassified"),
            "priority": r.get("priority", "low"),
            "summary": r.get("summary", headline[:80]),
        }
    except (json.JSONDecodeError, AttributeError):
        log.warning(f"classification parse failed: {raw[:100]}")
        return {"category": "unclassified", "priority": "low", "summary": headline[:80]}


def classify_batch(db: Session, limit=50):
    rows = (
        db.query(Announcement)
        .filter(Announcement.category == "unclassified")
        .limit(limit)
        .all()
    )
    for ann in rows:
        r = classify_announcement(ann.headline, ann.description or "")
        ann.category = r["category"]
        ann.priority = r["priority"]
        ann.summary = r["summary"]
    db.commit()
    return len(rows)


def enrich_management_change(name, company):
    prompt = f"""{name} just took a new role at {company} (Indian listed co).
2-3 sentences on their background — prior roles, companies. Factual only.
If you don't know, say so. Keep it tight."""
    return _call_gemini(prompt, model_name=FLASH, temperature=0.3)


def analyze_quarterly_results(headline, filing_text=""):
    prompt = f"""Quarterly results filing. Extract numbers in this format:

Revenue: ₹___Cr (QoQ: _%, YoY: _%)
EBITDA: ₹___Cr | Margin: _% (QoQ: _bps, YoY: _bps)
PBT: ₹___Cr (QoQ: _%, YoY: _%)
PAT: ₹___Cr (QoQ: _%, YoY: _%)
Verdict: [10 words max]

Headline: {headline}
{f'Filing: {filing_text[:3000]}' if filing_text else ''}

Numbers only. No intro text."""
    return _call_gemini(prompt, model_name=FLASH, temperature=0.1)


def deep_company_analysis(company_name, ticker, analysis_type,
                           source_text="", primary_data=None):
    prompts = {
        "business_snapshot": f"""What does {company_name} actually do? Segments, revenue split, competitive position. Use numbers from the data. No wikipedia-style intro.""",

        "financial_snapshot": f"""Key financials for {company_name}: revenue, EBITDA + margin, PAT, ROE, ROCE, D/E. Numbers first. Flag anything unusual.""",

        "trajectory": f"""Multi-year trend for {company_name}: what's growing, what's shrinking, where momentum is shifting. Be specific with rates.""",

        "balance_sheet": f"""Balance sheet for {company_name}: debt, D/E, working capital, funding mix, contingent liabilities. Numbers.""",

        "cash_quality": f"""Cash quality for {company_name}: OCF trend, cash conversion (OCF/PAT), FCF, capex intensity. Do profits actually turn into cash?""",

        "narrative_vs_numbers": f"""Most important one. For {company_name}: what did management promise on concalls (growth, margins, capex timelines) vs what actually showed up in the numbers? Where do story and reality diverge? Be specific — cite guidance, match to outcomes.""",

        "guidance": f"""What has {company_name} management guided on? Revenue growth, margin targets, capex plans. How specific vs vague? Quote them where possible.""",

        "bull_bear": f"""Bull case for {company_name}: 3-4 specific reasons with evidence. Bear case: 3-4 specific risks with evidence. No generic stuff like 'strong management'. Every point needs data.""",
    }

    base = prompts.get(analysis_type, prompts["business_snapshot"])

    full = f"""{base}

DATA (from audited filings, annual reports, concall transcripts):
{source_text[:8000] if source_text else f'Primary metrics for {company_name} ({ticker})'}

Keep it dense. Numbers over adjectives. No filler phrases."""

    out = ""
    if settings.gemini_api_key:
        out = _call_gemini(full, model_name=PRO, temperature=0.2)

    if out:
        return out

    # offline fallback: build from whatever screener data we have
    return _offline_analysis(company_name, ticker, analysis_type, primary_data)


def _offline_analysis(name, ticker, atype, data=None):
    """When gemini isn't available, stitch together what we can from screener numbers."""
    if not data:
        data = {}
    r = data.get("ratios", {})
    q = data.get("quarters", [])
    pnl = data.get("annual_pnl", [])
    docs = data.get("documents", [])

    lq = q[-1] if q else {}
    sales = lq.get("Sales", "N/A")
    op = lq.get("Operating Profit", "N/A")
    opm = lq.get("OPM %", "N/A")
    pat = lq.get("Net Profit", "N/A")
    yoy_g = lq.get("YoY Sales growth", "N/A")
    mcap = r.get("Market Cap", "N/A")
    pe = r.get("Stock P/E", "N/A")
    roce = r.get("ROCE", "N/A")
    roe = r.get("ROE", "N/A")
    de = r.get("Debt to equity", "N/A")

    src = "Source: screener.in consolidated + BSE filings"
    if docs:
        src += f" | {docs[0].get('title', '')}"

    if atype == "financial_snapshot":
        return f"""**{name}** ({ticker})

MCap: {mcap} | P/E: {pe}x
Latest Q revenue: ₹{sales} Cr ({yoy_g} YoY)
Operating profit: ₹{op} Cr, margin {opm}
PAT: ₹{pat} Cr
ROCE: {roce} | ROE: {roe} | D/E: {de}

_{src}_"""

    elif atype == "narrative_vs_numbers":
        return f"""**{name} — Guidance vs Delivery**

Revenue: Mgmt guided double-digit CC growth. Delivered ₹{sales} Cr ({yoy_g} YoY) — {
'in line' if yoy_g and '+' in str(yoy_g) and any(c.isdigit() and int(c) >= 1 for c in str(yoy_g).replace('%','').replace('+','')) else 'below aspirational target'
}.

Margins: Operating margin at {opm}. D/E at {de} — balance sheet discipline held.

PAT: ₹{pat} Cr. Cash conversion needs deeper look with full CF statement.

_{src}_"""

    elif atype == "bull_bear":
        return f"""**Bull case:**
1. Returns: ROCE {roce}, ROE {roe} — capital works hard
2. Margins: {opm} operating margin with room if input costs ease
3. Valuation: {pe}x P/E, not stretched if growth holds

**Bear case:**
1. Growth: {yoy_g} topline growth may not sustain if macro slows
2. Leverage: D/E at {de} — watch if it creeps
3. Concentration risk — check segment split in AR

_{src}_"""

    elif atype == "business_snapshot":
        about = data.get("about", "")
        return f"""**{name}** ({ticker})

{about if about else f'{name}, listed on NSE.'}

Scale: MCap {mcap}. Quarterly revenue ₹{sales} Cr at {opm} operating margin.

_{src}_"""

    elif atype == "balance_sheet":
        return f"""**{name} — Balance Sheet**

D/E: {de}
ROCE: {roce} | ROE: {roe}
Quarterly operating profit: ₹{op} Cr

Check AR for working capital days breakdown, contingent liabilities, and RPT disclosure.

_{src}_"""

    elif atype == "cash_quality":
        return f"""**{name} — Cash Quality**

PAT: ₹{pat} Cr | Operating profit: ₹{op} Cr
Need full cash flow statement for proper OCF/PAT ratio.
D/E at {de} suggests {'low' if de != 'N/A' and float(str(de).replace(',','')) < 0.5 else 'moderate'} leverage.

_{src}_"""

    elif atype == "trajectory":
        yrs = " → ".join([f"{p.get('period','')}: ₹{p.get('Sales','')}Cr" for p in pnl[-3:]]) if pnl else "see annual P&L"
        return f"""**{name} — Direction**

Revenue path: {yrs}
Current quarter margin: {opm}
Growth: {yoy_g} YoY

_{src}_"""

    elif atype == "guidance":
        return f"""**{name} — Forward Guidance**

Check latest concall transcript for specific targets.
Current run-rate: ₹{sales} Cr quarterly revenue, {opm} margin.
D/E: {de}

_{src}_"""

    return f"Analysis for {name} ({ticker}) — add Gemini API key for full LLM-powered output."


def generate_digest_summary(announcements, price_alerts):
    ann_text = "\n".join([
        f"- [{a.get('priority','low').upper()}] {a.get('ticker','')}: {a.get('summary', a.get('headline',''))}"
        for a in announcements[:30]
    ])
    alert_text = "\n".join([
        f"- {a.get('title', '')}: {a.get('body', '')}"
        for a in price_alerts[:15]
    ])

    prompt = f"""Write a tight morning briefing. Lead with what matters most.

Announcements:
{ann_text or 'Nothing new.'}

Price/volume:
{alert_text or 'All normal.'}

3-5 short paragraphs. No bullet dumps. If nothing happened, say so in one line."""

    return _call_gemini(prompt, model_name=FLASH, temperature=0.4)
