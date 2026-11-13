import httpx
from bs4 import BeautifulSoup
import re
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

# simple in-process cache so we don't spam screener during testing
_CACHE: Dict[str, Dict[str, Any]] = {}


def clean_ticker(ticker: str) -> str:
    return ticker.upper().replace(".NS", "").replace(".BO", "").strip()


def parse_num(val_str: str) -> Optional[float]:
    if not val_str:
        return None
    cleaned = val_str.replace(",", "").replace("%", "").replace("₹", "").strip()
    try:
        return float(cleaned)
    except ValueError:
        return None


def fetch_screener_data(symbol: str) -> Dict[str, Any]:
    sym = clean_ticker(symbol)
    if sym in _CACHE:
        return _CACHE[sym]
    
    url = f"https://www.screener.in/company/{sym}/consolidated/"
    html_content = ""
    
    try:
        with httpx.Client(headers=HEADERS, timeout=12.0, follow_redirects=True) as client:
            resp = client.get(url)
            if resp.status_code == 404:
                # some tickers only have standalone (no subsidiaries)
                url_standalone = f"https://www.screener.in/company/{sym}/"
                resp = client.get(url_standalone)
            if resp.status_code == 200:
                html_content = resp.text
    except Exception as e:
        logger.warning(f"screener fetch failed for {sym}: {e}")
    
    if not html_content:
        # return empty structure rather than mock data
        return {
            "symbol": sym,
            "name": sym,
            "about": "",
            "ratios": {},
            "quarters": [],
            "annual_pnl": [],
            "documents": [],
            "source": "screener.in (unavailable)",
        }

    soup = BeautifulSoup(html_content, "html.parser")
    
    # company name
    name_el = soup.find("h1")
    name = name_el.text.strip() if name_el else sym
    
    # about blurb
    about_el = soup.find("div", class_="about")
    about_text = ""
    if about_el:
        p_el = about_el.find("p")
        if p_el:
            about_text = p_el.text.strip()
            
    # top ratios bar
    ratios: Dict[str, Any] = {}
    ratio_top = soup.find("ul", id="top-ratios")
    if ratio_top:
        for li in ratio_top.find_all("li"):
            name_span = li.find("span", class_="name")
            val_span = li.find("span", class_="nowrap value")
            if name_span and val_span:
                k = name_span.text.strip()
                v = val_span.text.strip()
                ratios[k] = v

    # quarterly results table
    quarters: List[Dict[str, Any]] = []
    quarters_sec = soup.find("section", id="quarters")
    if quarters_sec:
        table = quarters_sec.find("table")
        if table:
            headers = [th.text.strip() for th in table.find("thead").find_all("th") if th.text.strip()]
            q_names = headers
            rows_data: Dict[str, List[str]] = {}
            for tr in table.find("tbody").find_all("tr"):
                cells = tr.find_all("td")
                if len(cells) > 1:
                    row_name = re.sub(r'\s*\+.*$', '', cells[0].text.strip())
                    row_vals = [c.text.strip() for c in cells[1:]]
                    rows_data[row_name] = row_vals
            
            n_quarters = len(q_names)
            for i in range(max(0, n_quarters - 5), n_quarters):
                q_label = q_names[i]
                q_dict = {"quarter": q_label}
                for metric, vals in rows_data.items():
                    if i < len(vals):
                        q_dict[metric] = vals[i]
                quarters.append(q_dict)

    # annual P&L
    annual_pnl: List[Dict[str, Any]] = []
    profit_sec = soup.find("section", id="profit-loss")
    if profit_sec:
        table = profit_sec.find("table")
        if table:
            years = [th.text.strip() for th in table.find("thead").find_all("th") if th.text.strip()]
            pnl_rows: Dict[str, List[str]] = {}
            for tr in table.find("tbody").find_all("tr"):
                cells = tr.find_all("td")
                if len(cells) > 1:
                    r_name = re.sub(r'\s*\+.*$', '', cells[0].text.strip())
                    pnl_rows[r_name] = [c.text.strip() for c in cells[1:]]
            
            for i in range(max(0, len(years) - 5), len(years)):
                y_label = years[i]
                y_dict = {"period": y_label}
                for metric, vals in pnl_rows.items():
                    if i < len(vals):
                        y_dict[metric] = vals[i]
                annual_pnl.append(y_dict)

    # concall transcripts, presentations, annual reports
    documents: List[Dict[str, str]] = []
    doc_sec = soup.find("section", id="documents")
    if doc_sec:
        for a in doc_sec.find_all("a", href=True):
            text = a.text.strip()
            href = a.get("href")
            if any(term in text.lower() for term in ["transcript", "concall", "annual report", "presentation"]):
                documents.append({
                    "title": text,
                    "url": href if href.startswith("http") else f"https://www.screener.in{href}"
                })

    result = {
        "symbol": sym,
        "name": name,
        "about": about_text,
        "ratios": ratios,
        "quarters": quarters,
        "annual_pnl": annual_pnl,
        "documents": documents[:8],
        "source": "screener.in",
    }
    _CACHE[sym] = result
    return result
